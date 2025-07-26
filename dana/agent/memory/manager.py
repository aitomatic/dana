import uuid
from datetime import datetime
from typing import Any

from dana.common.resource.base_resource import BaseResource
from dana.common.resource.llm.llm_resource import LLMResource

from .domain import MemoryItem, MemoryMetadata, MemoryType, StorageType
from .llm_integration import LLMIntentDetector, LLMMemoryExtractor, LLMMemoryRanker
from .repository import WorkingMemory


class MemoryManager(BaseResource):
    """Central orchestrator for all memory operations - MemOS Architecture with Dana LLM Integration"""

    def __init__(
        self,
        name: str,
        session_id: str | None = None,
        user_id: str | None = None,
        llm_resource: LLMResource | None = None,
        use_llamaindex: bool = False,
        use_json_storage: bool = True,
        storage_path: str = ".dana/memory",
        agent_id: str | None = None,
        instance_id: str | None = None,
    ):
        super().__init__(name)
        self.user_id = user_id or "default_user"
        self.session_id = session_id or uuid.uuid4().hex
        self.use_llamaindex = use_llamaindex
        self.use_json_storage = use_json_storage
        self.storage_path = storage_path

        # Initialize 3-level memory repositories (removed SharedMemory)
        # Extract agent_id and instance_id for new storage structure
        self.agent_id = agent_id or name  # Default to manager name
        self.instance_id = instance_id or self.session_id  # Default to session_id

        # Initialize persistent WorkingMemory with new path structure
        self.working_memory = WorkingMemory(
            user_id=self.user_id,
            session_id=self.session_id,
            agent_id=self.agent_id,
            instance_id=self.instance_id,
            max_items=50,
            storage_path=storage_path,
        )

        # Updated storage paths for LongTerm and User memory: user_id/agent_id/
        agent_storage_path = f"{storage_path}/agent_context_memory/{self.user_id}/{self.agent_id}"

        if use_llamaindex:
            from .llamaindex_repositories import LlamaIndexLongTermMemory, LlamaIndexUserMemory

            self.long_term_memory = LlamaIndexLongTermMemory(self.user_id, agent_storage_path)
            self.user_memory = LlamaIndexUserMemory(self.user_id, agent_storage_path)
            self.info("Initialized with LlamaIndex-based file storage repositories (3-level)")
        elif use_json_storage:
            from .json_repositories import JSONLongTermMemory, JSONUserMemory

            self.long_term_memory = JSONLongTermMemory(self.user_id, agent_storage_path)
            self.user_memory = JSONUserMemory(self.user_id, agent_storage_path)
            self.info("Initialized with JSON-based file storage repositories (3-level)")
        else:
            from .repository import LongTermMemory, UserMemory

            self.long_term_memory = LongTermMemory(self.user_id)
            self.user_memory = UserMemory(self.user_id)
            self.info("Initialized with default in-memory repositories (3-level)")

        # Batch processing configuration
        self.token_threshold = 8000  # Trigger batch processing when working memory token count reaches this size
        self.keep_recent_tokens = 2000  # Keep recent items totaling approximately this many tokens after batch processing

        # Initialize LLM-powered components
        self.llm_extractor = LLMMemoryExtractor(llm_resource)
        self.llm_intent_detector = LLMIntentDetector(llm_resource)
        self.llm_ranker = LLMMemoryRanker(llm_resource)

    def _count_tokens(self, text: str) -> int:
        """Simple token counting utility (approximation: 1 token ≈ 4 characters)"""
        # More sophisticated token counting could use tiktoken for OpenAI models
        # For now, use a simple approximation: 1 token ≈ 4 characters
        return len(text) // 4

    def _get_working_memory_token_count(self, memories: list[MemoryItem]) -> int:
        """Calculate total token count for a list of memory items"""
        total_text = "\n".join([memory.memory for memory in memories])
        return self._count_tokens(total_text)

    def _get_recent_items_by_token_limit(self, memories: list[MemoryItem], token_limit: int) -> list[MemoryItem]:
        """Get most recent items that fit within the token limit"""
        if not memories:
            return []

        # Start from the most recent items and work backwards
        recent_items = []
        current_tokens = 0

        # Process items in reverse order (most recent first)
        for memory in reversed(memories):
            item_tokens = self._count_tokens(memory.memory)
            if current_tokens + item_tokens <= token_limit:
                recent_items.insert(0, memory)  # Insert at beginning to maintain order
                current_tokens += item_tokens
            else:
                # If adding this item would exceed the limit, stop
                break

        return recent_items

    async def add_conversation_memory(self, memory_content: str) -> list[MemoryItem]:
        """Simplified memory addition - only add to WorkingMemory, batch process later"""
        # Create a simple memory item for immediate storage in WorkingMemory
        memory = MemoryItem(
            memory=memory_content,
            user_id=self.user_id,
            session_id=self.session_id,
            timestamp=datetime.now(),
            metadata=MemoryMetadata(
                memory_type=StorageType.WORKING_MEMORY,  # Default, will be classified during batch processing
                key="conversation",
                tags=["conversation"],
                embedding=[0.1],  # Placeholder
                confidence=1.0,
                type=MemoryType.TOPIC,  # Default, will be classified during batch processing
            ),
        )

        # Store in WorkingMemory only
        await self.working_memory.store(memory)

        # Check if we need to trigger batch processing based on token count
        current_items = await self.working_memory.search([], limit=100)  # Get all items to check token count
        current_token_count = self._get_working_memory_token_count(current_items)
        if current_token_count >= self.token_threshold:
            await self.process_working_memory_batch()

        return [memory]

    async def process_working_memory_batch(self):
        """Process WorkingMemory items in batch using LLM extraction"""
        try:
            # Get all items from working memory
            all_items = await self.working_memory.search([], limit=100)

            # Determine which recent items to keep based on token limit
            items_to_keep = self._get_recent_items_by_token_limit(all_items, self.keep_recent_tokens)

            if len(all_items) <= len(items_to_keep):
                # Not enough items to process (all items fit within keep_recent_tokens)
                return

            # Items to process (all except the recent ones we want to keep)
            items_to_process = [item for item in all_items if item not in items_to_keep]

            if not items_to_process:
                return

            # Log token count for batch processing
            token_count = self._get_working_memory_token_count(items_to_process)
            keep_tokens = self._get_working_memory_token_count(items_to_keep)
            self.info(
                f"Processing batch of {len(items_to_process)} items ({token_count} tokens), keeping {len(items_to_keep)} recent items ({keep_tokens} tokens)"
            )

            # Combine conversation content for batch LLM extraction
            combined_content = "\n".join([item.memory for item in items_to_process])

            # Use LLM to extract and classify memories
            extracted_memories = await self.llm_extractor.extract_memories(combined_content, self.user_id)

            # Process extracted memories and store in appropriate repositories
            for mem_dict in extracted_memories:
                # Convert semantic_type string to MemoryType enum
                semantic_type_str = mem_dict.get("semantic_type", "TOPIC")
                try:
                    semantic_type = MemoryType[semantic_type_str]
                except KeyError:
                    semantic_type = MemoryType.TOPIC  # Default fallback

                # Determine correct StorageType enum value
                if mem_dict["memory_type"] == "LongTermMemory":
                    storage_type = StorageType.LONG_TERM_MEMORY
                elif mem_dict["memory_type"] == "UserMemory":
                    storage_type = StorageType.USER_MEMORY
                else:
                    storage_type = StorageType.WORKING_MEMORY

                memory = MemoryItem(
                    memory=mem_dict["value"],
                    user_id=self.user_id,
                    session_id=self.session_id,
                    timestamp=datetime.now(),
                    metadata=MemoryMetadata(
                        memory_type=storage_type,
                        key=mem_dict.get("key"),
                        tags=mem_dict.get("tags", []),
                        embedding=mem_dict.get("embedding", [0.1]),
                        confidence=mem_dict.get("confidence", 1.0),
                        type=semantic_type,
                    ),
                )

                # Store in appropriate persistent repository based on LLM classification
                if mem_dict["memory_type"] == "LongTermMemory":
                    await self.long_term_memory.store(memory)
                elif mem_dict["memory_type"] == "UserMemory":
                    await self.user_memory.store(memory)

            # Clear working memory and keep only recent items using token-based retention
            self.working_memory.replace_with_items(items_to_keep)

            self.info(
                f"Batch processed {len(items_to_process)} working memory items ({token_count} tokens), extracted {len(extracted_memories)} memories"
            )

        except Exception as e:
            self.error(f"Batch processing failed: {e}")

    async def manual_batch_process(self):
        """Manually trigger batch processing regardless of threshold"""
        await self.process_working_memory_batch()

    async def chat_with_memory(self, query: str) -> dict[str, Any]:
        """MemOS-style chat with real LLM intent detection and memory retrieval"""
        # Step 1: Get current working memory
        current_working = await self.working_memory.search([], 20)

        # Step 2: Real LLM intent detection - check if current context is sufficient
        intent_result = await self.llm_intent_detector.detect_intent(query, current_working)

        if intent_result.get("trigger_retrieval", False):
            # Step 3: Search persistent memories for missing evidence
            missing_evidence = intent_result.get("missing_evidence", [])
            retrieved_memories = await self._search_persistent_memories(missing_evidence)

            # Step 4: Real LLM reranking and update working memory
            await self._replace_working_memory_with_llm_ranking(query, current_working, retrieved_memories)

            # Get updated working memory
            enhanced_context = await self.working_memory.search([], 20)
        else:
            enhanced_context = current_working

        return {
            "context": enhanced_context,
            "intent_detected": intent_result,
            "response": f"Response based on {len(enhanced_context)} memories",
            "llm_powered": True,
            "llamaindex_enabled": self.use_llamaindex,
        }

    async def retrieve_context(self, query: str) -> list[str]:
        """Enhanced context retrieval with LlamaIndex text search or embedding search"""
        if self.use_llamaindex:
            # Use LlamaIndex text-based search for better semantic understanding
            wm = await self.working_memory.search([], 5)  # Working memory still uses list approach
            ltm = await self.long_term_memory.search_by_text(query, 10)
            um = await self.user_memory.search_by_text(query, 10)
        else:
            # Fallback to embedding-based search
            query_embedding = [0.1]  # Placeholder
            wm = await self.working_memory.search(query_embedding, 5)
            ltm = await self.long_term_memory.search(query_embedding, 10)
            um = await self.user_memory.search(query_embedding, 10)

        # Combine and rank by relevance using LLM (3-level architecture)
        all_memories = wm + ltm + um
        ranked_memories = await self.llm_ranker.rank_memories(query, all_memories)
        return [memory.memory for memory in ranked_memories]

    async def get_user_profile(self) -> dict[str, Any]:
        """Get comprehensive user profile from UserMemory with optional LlamaIndex summary"""
        if self.use_llamaindex and hasattr(self.user_memory, "get_user_profile_summary"):
            try:
                profile_summary = await self.user_memory.get_user_profile_summary()
                memories = await self.user_memory.search_by_text("", 100)
            except Exception as e:
                self.error(f"Failed to get LlamaIndex profile summary: {e}")
                profile_summary = "Error generating profile summary"
                memories = await self.user_memory.search([], 100)
        else:
            profile_summary = "Basic profile (LlamaIndex disabled)"
            memories = await self.user_memory.search([], 100)

        return {
            "user_id": self.user_id,
            "profile_summary": profile_summary,
            "profile_memories": [m.memory for m in memories],
            "memory_stats": {
                "total_user_memories": len(memories),
                "memory_types": [m.metadata.type.value for m in memories],
                "llamaindex_enabled": self.use_llamaindex,
                "llm_enhanced": True,
            },
        }

    async def advanced_query(self, query: str, memory_type: str = "long_term") -> str:
        """Advanced querying using LlamaIndex query engine (only available with LlamaIndex)"""
        if not self.use_llamaindex:
            return "Advanced queries require LlamaIndex to be enabled"

        try:
            if memory_type == "long_term":
                query_engine = self.long_term_memory.get_query_engine()
            elif memory_type == "user_memory":
                query_engine = self.user_memory.get_query_engine()
            else:
                return "Invalid memory type. Use 'long_term' or 'user_memory'"

            if not query_engine:
                return f"Query engine not available for {memory_type}"

            response = query_engine.query(query)

            # Handle different response types
            if hasattr(response, "response"):
                return str(response.response)
            else:
                return str(response)

        except Exception as e:
            self.error(f"Advanced query failed: {e}")
            return f"Query failed: {str(e)}"

    async def search_by_text(self, query: str, memory_type: str = "all", limit: int = 10) -> list[MemoryItem]:
        """Text-based search across memory types (works with JSON and LlamaIndex repositories)"""
        results = []

        try:
            if memory_type in ["all", "long_term"]:
                if hasattr(self.long_term_memory, "search_by_text"):
                    ltm_results = await self.long_term_memory.search_by_text(query, limit)
                    results.extend(ltm_results)

            if memory_type in ["all", "user"]:
                if hasattr(self.user_memory, "search_by_text"):
                    um_results = await self.user_memory.search_by_text(query, limit)
                    results.extend(um_results)

            if memory_type in ["all", "working"]:
                # Simple text search for working memory
                working_memories = await self.working_memory.search([], limit=20)
                query_lower = query.lower()
                working_results = [m for m in working_memories if query_lower in m.memory.lower()]
                results.extend(working_results)

            # Sort by relevance and limit results
            return results[:limit]

        except Exception as e:
            self.error(f"Error in text search: {e}")
            return []

    async def get_current_working_memory_tokens(self) -> int:
        """Get current token count in WorkingMemory"""
        current_items = await self.working_memory.search([], limit=100)
        return self._get_working_memory_token_count(current_items)

    async def get_memory_statistics(self) -> dict[str, Any]:
        """Get comprehensive memory statistics across all repositories"""
        storage_type = "JSON" if self.use_json_storage else ("LlamaIndex" if self.use_llamaindex else "In-Memory")
        stats = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "storage_backend": storage_type,
            "llamaindex_enabled": self.use_llamaindex,
            "json_storage_enabled": self.use_json_storage,
            "storage_path": self.storage_path,
            "token_threshold": self.token_threshold,
        }

        try:
            # Working memory stats
            working_memories = await self.working_memory.search([], 100)
            current_tokens = self._get_working_memory_token_count(working_memories)
            stats["working_memory"] = {
                "count": len(working_memories),
                "max_capacity": getattr(self.working_memory, "max_items", 20),
                "current_tokens": current_tokens,
                "token_threshold": self.token_threshold,
                "keep_recent_tokens": self.keep_recent_tokens,
            }

            # Long-term memory stats
            if self.use_llamaindex and hasattr(self.long_term_memory, "get_memory_count"):
                stats["long_term_memory"] = {"count": self.long_term_memory.get_memory_count(), "storage_type": "LlamaIndex file-based"}
            else:
                ltm_memories = await self.long_term_memory.search([], 1000)
                stats["long_term_memory"] = {"count": len(ltm_memories), "storage_type": "In-memory"}

            # User memory stats
            if self.use_llamaindex and hasattr(self.user_memory, "get_memory_count"):
                stats["user_memory"] = {"count": self.user_memory.get_memory_count(), "storage_type": "LlamaIndex file-based"}
            else:
                um_memories = await self.user_memory.search([], 1000)
                stats["user_memory"] = {"count": len(um_memories), "storage_type": "In-memory"}

            # No shared memory in 3-level architecture

        except Exception as e:
            self.error(f"Failed to get memory statistics: {e}")
            stats["error"] = str(e)

        return stats

    async def _search_persistent_memories(self, missing_evidence: list[str]) -> list[MemoryItem]:
        """Search both LongTermMemory and UserMemory for missing evidence"""
        all_results = []

        for evidence in missing_evidence:
            if self.use_llamaindex:
                ltm_results = await self.long_term_memory.search_by_text(evidence, 5)
                um_results = await self.user_memory.search_by_text(evidence, 5)
            else:
                embedding = [0.1]  # Placeholder
                ltm_results = await self.long_term_memory.search(embedding, 5)
                um_results = await self.user_memory.search(embedding, 5)

            all_results.extend(ltm_results + um_results)

        return all_results

    async def _replace_working_memory_with_llm_ranking(self, query: str, original: list[MemoryItem], retrieved: list[MemoryItem]) -> None:
        """Replace working memory with LLM-ranked combination"""
        combined = original + retrieved

        # Use LLM to rank the combined memories
        ranked_memories = await self.llm_ranker.rank_memories(query, combined)

        # Take top 10 most relevant
        top_memories = ranked_memories[:10]

        # Clear and repopulate working memory
        self.working_memory = WorkingMemory(self.user_id, self.session_id, max_items=20)
        for memory in top_memories:
            await self.working_memory.store(memory)
