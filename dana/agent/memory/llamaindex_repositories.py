"""
LlamaIndex-based Memory Repositories with File-based Vector Search

This module provides LlamaIndex implementations for the three main memory types:
- LongTermMemory: Persistent storage with semantic deduplication
- UserMemory: Unlimited profile storage for personal information
- SharedMemory: Collective knowledge with privacy controls

All implementations use file-based storage with vector search capabilities.
"""

import json
import threading
from datetime import datetime
from pathlib import Path

from llama_index.core import Document, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from llama_index.embeddings.openai import OpenAIEmbedding, OpenAIEmbeddingModelType

from dana.agent.memory.domain import MemoryItem, MemoryType, StorageType
from dana.agent.memory.repository import BaseMemoryRepository
from dana.common.mixins.loggable import Loggable


class LlamaIndexBaseRepository(BaseMemoryRepository, Loggable):
    """Base class for LlamaIndex-powered memory repositories"""

    def __init__(
        self,
        storage_path: str,
        repository_name: str,
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536,
        similarity_threshold: float = 0.8,
    ):
        super().__init__()
        self.storage_path = Path(storage_path)
        self.repository_name = repository_name
        self.similarity_threshold = similarity_threshold

        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize embedding model
        self.embed_model = OpenAIEmbedding(model=OpenAIEmbeddingModelType.TEXT_EMBED_3_SMALL, dimensions=embedding_dimensions)

        # Initialize LlamaIndex components
        self.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        self.index: VectorStoreIndex | None = None
        self.retriever: VectorIndexRetriever | None = None

        # Memory storage for metadata
        self.memories: dict[str, MemoryItem] = {}
        self.memory_metadata_file = self.storage_path / "memory_metadata.json"

        # Thread safety
        self._lock = threading.RLock()

        # Initialize index
        self._initialize_index()

        self.info(f"LlamaIndex {repository_name} repository initialized at {self.storage_path}")

    def _initialize_index(self):
        """Initialize or load existing LlamaIndex vector store"""
        try:
            with self._lock:
                # Try to load existing index
                if (self.storage_path / "docstore.json").exists():
                    storage_context = StorageContext.from_defaults(persist_dir=str(self.storage_path))
                    self.index = load_index_from_storage(storage_context)
                    self.info(f"Loaded existing {self.repository_name} vector store")
                else:
                    # Create new index
                    self.index = VectorStoreIndex(nodes=[], embed_model=self.embed_model, show_progress=True)
                    self.index.storage_context.persist(persist_dir=str(self.storage_path))
                    self.info(f"Created new {self.repository_name} vector store")

                # Initialize retriever only if index exists
                if self.index is not None:
                    self.retriever = VectorIndexRetriever(
                        index=self.index,
                        similarity_top_k=10,
                        vector_store_query_mode=VectorStoreQueryMode.MMR,
                        vector_store_kwargs={"mmr_threshold": 0.5},
                    )

                # Load memory metadata
                self._load_memory_metadata()

        except Exception as e:
            self.error(f"Failed to initialize {self.repository_name} vector store: {e}")
            raise

    def _load_memory_metadata(self):
        """Load memory metadata from file"""
        if self.memory_metadata_file.exists():
            try:
                with open(self.memory_metadata_file) as f:
                    metadata = json.load(f)
                    for mem_id, mem_data in metadata.items():
                        # Reconstruct MemoryItem from saved data
                        memory = MemoryItem(
                            memory=mem_data["memory"],
                            user_id=mem_data["user_id"],
                            timestamp=datetime.fromisoformat(mem_data["timestamp"]),
                            session_id=mem_data.get("session_id"),
                            id=mem_data["id"],
                        )
                        # Reconstruct metadata
                        if "metadata" in mem_data:
                            meta = mem_data["metadata"]
                            memory.metadata.memory_type = StorageType(meta.get("memory_type", "WorkingMemory"))
                            memory.metadata.key = meta.get("key")
                            memory.metadata.tags = meta.get("tags", [])
                            memory.metadata.embedding = meta.get("embedding")
                            memory.metadata.confidence = meta.get("confidence")
                            memory.metadata.entities = meta.get("entities", [])
                            memory.metadata.type = MemoryType(meta.get("type", "fact"))

                        self.memories[mem_id] = memory

                self.info(f"Loaded {len(self.memories)} memory items for {self.repository_name}")
            except Exception as e:
                self.error(f"Failed to load memory metadata for {self.repository_name}: {e}")

    def _save_memory_metadata(self):
        """Save memory metadata to file"""
        try:
            metadata = {}
            for mem_id, memory in self.memories.items():
                metadata[mem_id] = {
                    "id": memory.id,
                    "memory": memory.memory,
                    "user_id": memory.user_id,
                    "timestamp": memory.timestamp.isoformat(),
                    "session_id": memory.session_id,
                    "metadata": {
                        "memory_type": memory.metadata.memory_type.value,
                        "key": memory.metadata.key,
                        "tags": memory.metadata.tags,
                        "embedding": memory.metadata.embedding,
                        "confidence": memory.metadata.confidence,
                        "entities": memory.metadata.entities,
                        "type": memory.metadata.type.value,
                    },
                }

            with open(self.memory_metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            self.debug(f"Saved {len(self.memories)} memory items for {self.repository_name}")
        except Exception as e:
            self.error(f"Failed to save memory metadata for {self.repository_name}: {e}")

    def _create_document_from_memory(self, memory: MemoryItem) -> Document:
        """Create LlamaIndex document from memory item"""
        return Document(
            text=memory.memory,
            metadata={
                "memory_id": memory.id,
                "user_id": memory.user_id,
                "session_id": memory.session_id,
                "timestamp": memory.timestamp.isoformat(),
                "memory_type": memory.metadata.memory_type.value,
                "semantic_type": memory.metadata.type.value,
                "tags": memory.metadata.tags,
                "confidence": memory.metadata.confidence,
                "key": memory.metadata.key,
                "entities": memory.metadata.entities,
            },
        )

    async def store(self, memory: MemoryItem) -> bool:
        """Store a memory item with LlamaIndex indexing"""
        try:
            with self._lock:
                if self.index is None:
                    self.error("Index not initialized, cannot store memory")
                    return False

                # Create LlamaIndex document
                document = self._create_document_from_memory(memory)

                # Parse document into nodes
                nodes = self.node_parser.get_nodes_from_documents([document])

                # Add to index
                self.index.insert_nodes(nodes)

                # Store memory metadata
                self.memories[memory.id] = memory

                # Persist changes
                self.index.storage_context.persist(persist_dir=str(self.storage_path))
                self._save_memory_metadata()

                self.debug(f"Stored memory {memory.id} in {self.repository_name}")
                return True

        except Exception as e:
            self.error(f"Failed to store memory {memory.id} in {self.repository_name}: {e}")
            return False

    async def search(self, query_embedding: list[float], limit: int) -> list[MemoryItem]:
        """Search memories using vector similarity (backwards compatibility)"""
        # For backwards compatibility, we'll return most recent memories
        # In practice, you'd want to implement actual embedding-based search
        with self._lock:
            sorted_memories = sorted(self.memories.values(), key=lambda m: m.timestamp, reverse=True)
            return sorted_memories[:limit]

    async def search_by_text(self, query: str, limit: int) -> list[MemoryItem]:
        """Search memories using text query (preferred LlamaIndex approach)"""
        try:
            with self._lock:
                if not self.retriever or not query.strip():
                    return []

                # Configure retriever for this search
                self.retriever.similarity_top_k = limit

                # Retrieve relevant nodes
                nodes = self.retriever.retrieve(query)

                # Convert nodes back to memory items
                result_memories = []
                for node in nodes:
                    memory_id = node.metadata.get("memory_id")
                    if memory_id and memory_id in self.memories:
                        result_memories.append(self.memories[memory_id])

                self.debug(f"Found {len(result_memories)} memories for query in {self.repository_name}")
                return result_memories

        except Exception as e:
            self.error(f"Failed to search memories by text in {self.repository_name}: {e}")
            return []

    async def retrieve(self, memory_id: str) -> MemoryItem | None:
        """Retrieve a specific memory by ID"""
        with self._lock:
            return self.memories.get(memory_id)

    def get_query_engine(self, similarity_top_k: int = 10):
        """Get a LlamaIndex query engine for advanced querying"""
        try:
            with self._lock:
                if not self.index:
                    return None

                return self.index.as_query_engine(
                    embed_model=self.embed_model,
                    similarity_top_k=similarity_top_k,
                    vector_store_query_mode=VectorStoreQueryMode.MMR,
                    vector_store_kwargs={"mmr_threshold": 0.5},
                )
        except Exception as e:
            self.error(f"Failed to create query engine for {self.repository_name}: {e}")
            return None

    def get_memory_count(self) -> int:
        """Get total number of memories stored"""
        with self._lock:
            return len(self.memories)


class LlamaIndexLongTermMemory(LlamaIndexBaseRepository):
    """LlamaIndex-powered long-term memory with semantic deduplication"""

    def __init__(self, user_id: str, storage_path: str = ".dana/memory"):
        storage_path = f"{storage_path}/{user_id}/long_term_llamaindex"
        super().__init__(
            storage_path=storage_path,
            repository_name="LongTermMemory",
            similarity_threshold=0.85,  # Higher threshold for deduplication
        )
        self.user_id = user_id

    async def store(self, memory: MemoryItem) -> bool:
        """Store with semantic deduplication"""
        try:
            # Check for similar existing memories to avoid duplicates
            similar_memories = await self.search_by_text(memory.memory, limit=5)

            # Simple deduplication - don't store if very similar content exists
            for existing_memory in similar_memories:
                if self._is_semantic_duplicate(memory.memory, existing_memory.memory):
                    self.debug(f"Skipping duplicate memory: {memory.id}")
                    return False

            return await super().store(memory)

        except Exception as e:
            self.error(f"Failed to store memory with deduplication: {e}")
            return False

    def _is_semantic_duplicate(self, new_content: str, existing_content: str) -> bool:
        """Check if content is semantically duplicate"""
        # Simple implementation - in production, use embedding similarity
        new_words = set(new_content.lower().split())
        existing_words = set(existing_content.lower().split())

        # Calculate Jaccard similarity
        intersection = len(new_words.intersection(existing_words))
        union = len(new_words.union(existing_words))

        if union == 0:
            return False

        similarity = intersection / union
        return similarity > self.similarity_threshold


class LlamaIndexUserMemory(LlamaIndexBaseRepository):
    """LlamaIndex-powered user memory for profile information"""

    def __init__(self, user_id: str, storage_path: str = ".dana/memory"):
        storage_path = f"{storage_path}/{user_id}/user_memory_llamaindex"
        super().__init__(storage_path=storage_path, repository_name="UserMemory", similarity_threshold=0.7)
        self.user_id = user_id

    async def get_user_profile_summary(self, query: str = "user preferences and characteristics") -> str:
        """Get a comprehensive user profile summary using LlamaIndex query engine"""
        try:
            query_engine = self.get_query_engine(similarity_top_k=20)
            if not query_engine:
                return "No profile information available"

            response = query_engine.query(
                f"Summarize what is known about this user based on their {query}. "
                f"Include preferences, characteristics, goals, and any personal information."
            )

            # Handle different response types
            if hasattr(response, "response"):
                return str(response.response)
            else:
                return str(response)

        except Exception as e:
            self.error(f"Failed to generate user profile summary: {e}")
            return "Error generating profile summary"

    async def search_user_preferences(self, topic: str, limit: int = 10) -> list[MemoryItem]:
        """Search for user preferences on a specific topic"""
        query = f"user preferences opinions likes dislikes {topic}"
        return await self.search_by_text(query, limit)


class LlamaIndexSharedMemory(LlamaIndexBaseRepository):
    """LlamaIndex-powered shared memory for collective knowledge"""

    # Class-level shared storage path
    _shared_storage_path = ".dana/memory/shared_llamaindex"
    _instance = None
    _lock = threading.Lock()
    _max_items = 50000

    def __new__(cls):
        """Singleton pattern for shared memory"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if not self._initialized:
            super().__init__(storage_path=self._shared_storage_path, repository_name="SharedMemory", similarity_threshold=0.8)
            self._initialized = True

    async def store(self, memory: MemoryItem) -> bool:
        """Store with capacity limits and privacy controls"""
        try:
            with self._lock:
                # Check capacity limits
                if len(self.memories) >= self._max_items:
                    # Remove oldest memories
                    oldest_memories = sorted(self.memories.values(), key=lambda m: m.timestamp)

                    # Remove oldest 10% when at capacity
                    remove_count = max(1, self._max_items // 10)
                    for old_memory in oldest_memories[:remove_count]:
                        del self.memories[old_memory.id]

                    # Rebuild index (expensive operation, consider optimization)
                    await self._rebuild_index()

                # Apply privacy filtering before storing
                if self._should_store_in_shared(memory):
                    return await super().store(memory)
                else:
                    self.debug(f"Memory {memory.id} filtered out for privacy reasons")
                    return False

        except Exception as e:
            self.error(f"Failed to store memory in shared repository: {e}")
            return False

    def _should_store_in_shared(self, memory: MemoryItem) -> bool:
        """Apply privacy controls to determine if memory should be shared"""
        # Simple privacy rules - extend as needed
        content_lower = memory.memory.lower()

        # Don't share personal information
        personal_indicators = [
            "my name is",
            "i am",
            "i'm",
            "my phone",
            "my email",
            "my address",
            "password",
            "personal",
            "private",
            "secret",
            "confidential",
        ]

        if any(indicator in content_lower for indicator in personal_indicators):
            return False

        # Don't share memories with low confidence
        if memory.metadata.confidence and memory.metadata.confidence < 0.7:
            return False

        return True

    async def _rebuild_index(self):
        """Rebuild the index with current memories (expensive operation)"""
        try:
            # Create new index
            documents = [self._create_document_from_memory(memory) for memory in self.memories.values()]

            if documents:
                nodes = []
                for doc in documents:
                    nodes.extend(self.node_parser.get_nodes_from_documents([doc]))

                self.index = VectorStoreIndex(nodes=nodes, embed_model=self.embed_model, show_progress=True)

                # Update retriever
                self.retriever = VectorIndexRetriever(
                    index=self.index,
                    similarity_top_k=10,
                    vector_store_query_mode=VectorStoreQueryMode.MMR,
                    vector_store_kwargs={"mmr_threshold": 0.5},
                )

                # Persist
                self.index.storage_context.persist(persist_dir=str(self.storage_path))
                self._save_memory_metadata()

                self.info(f"Rebuilt shared memory index with {len(self.memories)} memories")

        except Exception as e:
            self.error(f"Failed to rebuild shared memory index: {e}")

    async def search_collective_knowledge(self, query: str, limit: int = 10) -> list[MemoryItem]:
        """Search collective knowledge across all users"""
        return await self.search_by_text(f"collective knowledge {query}", limit)

    async def get_popular_topics(self, limit: int = 10) -> list[str]:
        """Get most popular topics in shared memory"""
        try:
            with self._lock:
                # Count tag frequencies
                tag_counts = {}
                for memory in self.memories.values():
                    for tag in memory.metadata.tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1

                # Return most popular tags
                popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
                return [tag for tag, count in popular_tags[:limit]]

        except Exception as e:
            self.error(f"Failed to get popular topics: {e}")
            return []
