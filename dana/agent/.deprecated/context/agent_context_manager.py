"""
Agent Context Manager for Dana Agents

This module provides the core context management system that enables
implicit context tracking and injection for Dana agents.
"""

from typing import Any
import os

from .conversation_state import ConversationState


class AgentContextManager:
    """
    Manages conversation context for Dana agents.

    Provides implicit context tracking, automatic prompt enhancement,
    and seamless conversation continuity without explicit memory calls.
    """

    def __init__(self, agent_instance, user_id: str = None, session_id: str = None, instance_id: str = None):
        self.agent = agent_instance

        # Phase 3: Ensure consistent user identity across script runs
        resolved_user_id = self._resolve_user_identity(user_id)
        resolved_session_id = self._resolve_session_identity(session_id)
        resolved_instance_id = self._resolve_instance_identity(instance_id)

        # Get agent struct name for shared memory
        self.agent_struct_name = (
            getattr(agent_instance, "_type", {}).name if hasattr(getattr(agent_instance, "_type", {}), "name") else "unknown"
        )

        self.conversation_state = ConversationState(
            user_id=resolved_user_id, session_id=resolved_session_id, agent_id=self.agent_struct_name, instance_id=resolved_instance_id
        )

        # Store original methods for wrapping
        self._original_solve = None
        self._original_reason = None

        # Initialize simplified 3-level memory system
        self._memory_manager = None
        self._initialize_simplified_memory_system()

        # Initialize cross-session persistence
        self._initialize_cross_session_persistence()

        # Initialize context management
        self._wrap_agent_methods()

    def _resolve_user_identity(self, provided_user_id: str = None) -> str:
        """Resolve user identity using SandboxContext state (Dana-native approach)"""
        import os
        import uuid

        # Priority 1: Use provided user_id
        if provided_user_id:
            return provided_user_id

        # Priority 2: Check Dana sandbox context for user_id
        if hasattr(self.agent, "_context") and self.agent._context:
            context_user_id = self.agent._context.get("system:user_id")
            if context_user_id:
                return context_user_id

        # Priority 3: Use environment variable
        env_user_id = os.getenv("DANA_USER_ID")
        if env_user_id:
            return env_user_id

        # Priority 4: Generate new user_id and store in context
        new_user_id = str(uuid.uuid4())

        # Store in sandbox context for future use
        if hasattr(self.agent, "_context") and self.agent._context:
            self.agent._context.set("system:user_id", new_user_id)

        return new_user_id

    def _resolve_instance_identity(self, provided_instance_id: str = None) -> str:
        """Resolve agent instance identity using SandboxContext state"""
        import os
        import uuid

        # Priority 1: Use provided instance_id
        if provided_instance_id:
            return provided_instance_id

        # Priority 2: Check agent instance for instance_id field
        if hasattr(self.agent, "instance_id") and self.agent.instance_id:
            return str(self.agent.instance_id)

        # Priority 3: Check Dana sandbox context for agent_instance_id
        if hasattr(self.agent, "_context") and self.agent._context:
            context_instance_id = self.agent._context.get("system:agent_instance_id")
            if context_instance_id:
                return context_instance_id

        # Priority 4: Use environment variable
        env_instance_id = os.getenv("DANA_AGENT_INSTANCE_ID")
        if env_instance_id:
            return env_instance_id

        # Priority 5: Generate new instance_id and store in context
        new_instance_id = str(uuid.uuid4())

        # Store in sandbox context for future use
        if hasattr(self.agent, "_context") and self.agent._context:
            self.agent._context.set("system:agent_instance_id", new_instance_id)

        return new_instance_id

    def _resolve_session_identity(self, provided_session_id: str = None) -> str:
        """Resolve session identity using SandboxContext state (Dana-native approach)"""
        import uuid

        # Priority 1: Use provided session_id
        if provided_session_id:
            return provided_session_id

        # Priority 2: Check Dana sandbox context for session_id
        if hasattr(self.agent, "_context") and self.agent._context:
            context_session_id = self.agent._context.get("system:session_id")
            if context_session_id:
                return context_session_id

        # Priority 3: Generate new session_id and store in context
        new_session_id = str(uuid.uuid4())

        # Store in sandbox context for future use
        if hasattr(self.agent, "_context") and self.agent._context:
            self.agent._context.set("system:session_id", new_session_id)

        return new_session_id

    def _initialize_simplified_memory_system(self):
        """Initialize the simplified 3-level Dana memory system"""
        # Check if the agent has memory enabled
        memory_enabled = getattr(self.agent, "memory_enabled", False)
        if not memory_enabled:
            self._memory_manager = None
            return

        try:
            from dana.agent.memory.manager import MemoryManager

            # Get LLM resource from agent context if available
            llm_resource = None
            if hasattr(self.agent, "_context") and self.agent._context:
                llm_resource = self.agent._context.get("system:llm_resource")
            dana_path = os.getenv("DANAPATH", "")
            print(f"dana_path: {dana_path}")
            # Initialize single memory manager with 3-level architecture and new storage paths
            self._memory_manager = MemoryManager(
                name=f"agent_memory_{self.agent_struct_name}_{self.conversation_state.instance_id}",
                session_id=self.conversation_state.session_id,
                user_id=self.conversation_state.user_id,
                llm_resource=llm_resource,
                use_llamaindex=True,
                use_json_storage=True,
                storage_path=os.path.join(dana_path, ".dana"),
                agent_id=self.agent_struct_name,
                instance_id=self.conversation_state.instance_id,
            )

            # Start memory manager
            if hasattr(self._memory_manager, "start"):
                self._memory_manager.start()

            print("Simplified 3-level memory system initialized")

        except ImportError as e:
            # Memory system not available, fall back to basic context
            print(f"Memory system not available: {e}")
            self._memory_manager = None
        except Exception as e:
            # Handle other initialization errors
            print(f"Memory system initialization failed: {e}")
            self._memory_manager = None

    def _initialize_cross_session_persistence(self):
        """Initialize cross-session persistence for Phase 3 functionality"""
        try:
            if self._memory_manager:
                # Phase 3: Restore context from previous sessions
                self._restore_session_context()
                print("Phase 3: Cross-session persistence initialized")
            else:
                print("Phase 3: Memory system not available, cross-session persistence disabled")
        except Exception as e:
            print(f"Phase 3: Cross-session persistence initialization failed: {e}")

    def _restore_session_context(self):
        """Restore context from previous sessions using memory system"""
        try:
            if not self._memory_manager:
                return

            # Get user profile and long-term context
            user_profile = self._run_async_safely(self._memory_manager.get_user_profile())

            # Build working memory with relevant persistent context
            if user_profile and user_profile.get("profile_memories"):
                print(f"Phase 3: Restoring {len(user_profile['profile_memories'])} user memories")

                # Create a context restoration prompt
                restoration_query = f"Starting new session for user {self.conversation_state.user_id}"

                # Get relevant context for this session
                relevant_context = self._run_async_safely(self._memory_manager.chat_with_memory(restoration_query))

                if relevant_context and relevant_context.get("context"):
                    print(f"Phase 3: Restored {len(relevant_context['context'])} relevant memories")

                    # Store restoration info in conversation state
                    self.conversation_state.extracted_facts["session_restored"] = True
                    self.conversation_state.extracted_facts["restored_memories"] = len(relevant_context["context"])

        except Exception as e:
            print(f"Phase 3: Session context restoration failed: {e}")

    def _wrap_agent_methods(self):
        """Wrap agent methods with context management"""
        if hasattr(self.agent, "solve"):
            self._original_solve = self.agent.solve
            self.agent.solve = self._context_aware_solve

        # Wrap reason function if it exists
        if hasattr(self.agent, "_reason_function"):
            self._original_reason = self.agent._reason_function
            self.agent._reason_function = self._context_aware_reason

    def _context_aware_solve(self, input_data: str, context: str | None = None) -> str:
        """Enhanced solve method with automatic context injection"""

        # Phase 2: Use memory system if available
        if self._memory_manager:
            return self._solve_with_memory_system(input_data, context)
        else:
            # Phase 1: Fallback to basic context management
            return self._solve_with_basic_context(input_data, context)

    def _solve_with_memory_system(self, input_data: str, context: str | None = None) -> str:
        """Enhanced solve method using input parameter enhancement"""

        # Get the original solve method from agent
        original_solve_method = self.agent._type.get_method("solve")

        # Call original solve method with enhanced input
        if original_solve_method:
            try:
                # Enhance input with memory context if available
                if self._memory_manager:
                    enhanced_input = self._build_memory_enhanced_input(input_data)
                else:
                    enhanced_input = input_data

                response = self.agent._call_method(original_solve_method, enhanced_input, context)
                response = str(response)
            except Exception as e:
                # Fallback if calling method fails
                response = f"I understand you said: {input_data} (Error: {e})"
        else:
            # Fallback if original solve doesn't exist
            response = f"I understand you said: {input_data}"

        # Store the complete interaction in simplified memory system
        try:
            complete_conversation = f"User: {input_data}\nAgent: {response}"
            self._store_interaction_in_memory(input_data, response, complete_conversation)
        except Exception as e:
            print(f"Memory storage error: {e}")

        # Also store in conversation state for compatibility
        self.conversation_state.add_turn(user_input=input_data, agent_response=response, context_used={})

        return response

    def _get_memory_context(self, input_data: str) -> dict:
        """Get context from simplified 3-level memory system"""
        try:
            if hasattr(self._memory_manager, "chat_with_memory"):
                return self._run_async_safely(self._memory_manager.chat_with_memory(input_data))
        except Exception as e:
            print(f"Memory system error: {e}")
        return {}

    def _store_interaction_in_memory(self, input_data: str, response: str, complete_conversation: str):
        """Store interaction in simplified memory system"""
        try:
            # Simply add to WorkingMemory - batch processing will handle LLM extraction
            if hasattr(self._memory_manager, "add_conversation_memory"):
                self._run_async_safely(self._memory_manager.add_conversation_memory(complete_conversation))
        except Exception as e:
            print(f"Memory storage error: {e}")

    def _solve_with_basic_context(self, input_data: str, context: str | None = None) -> str:
        """Basic solve method with Phase 1 context management"""

        # Extract user information from input
        self.conversation_state.extract_user_info(input_data)

        # Build context-enhanced prompt
        enhanced_prompt = self._build_contextual_prompt(input_data)

        # Get the original solve method from agent
        original_solve_method = self.agent._type.get_method("solve")

        # Call original solve method with enhanced prompt
        if original_solve_method:
            try:
                response = self.agent._call_method(original_solve_method, enhanced_prompt, context)
                response = str(response)
            except Exception as e:
                # Fallback if calling method fails
                response = f"I understand you said: {input_data} (Error: {e})"
        else:
            # Fallback if original solve doesn't exist
            response = f"I understand you said: {input_data}"

        # Store the interaction
        self.conversation_state.add_turn(
            user_input=input_data, agent_response=response, context_used=self.conversation_state.get_user_context()
        )

        return response

    def _context_aware_reason(self, prompt: str, **kwargs) -> str:
        """Enhanced reason function with context injection"""

        # Start with the original prompt
        enhanced_prompt = prompt

        # Add memory context if available
        if hasattr(self.agent, "_context") and self.agent._context:
            memory_context = self.agent._context.get("system:memory_context")
            if memory_context:
                enhanced_prompt = f"[Previous Conversation Context]\n{memory_context}\n\n[Current Task]\n{prompt}"

        # Add additional context if available
        if self.conversation_state.should_include_context():
            enhanced_prompt = self._enhance_prompt_with_context(enhanced_prompt)

        # Call original reason function
        if self._original_reason:
            return self._original_reason(enhanced_prompt, **kwargs)
        else:
            # Fallback for testing
            return f"Response to: {enhanced_prompt}"

    def _build_contextual_prompt(self, input_data: str) -> str:
        """Build a context-enhanced prompt for the agent"""

        # Get user context
        user_context = self.conversation_state.get_user_context()

        # Get conversation history
        conversation_context = self.conversation_state.get_conversation_context()

        # Build enhanced prompt
        prompt_parts = []

        # Add user information if available
        if user_context.get("user_info"):
            user_info = user_context["user_info"]
            info_parts = []

            if user_info.get("name"):
                info_parts.append(f"User name: {user_info['name']}")
            if user_info.get("email"):
                info_parts.append(f"User email: {user_info['email']}")

            if info_parts:
                prompt_parts.append(f"[User Information: {'; '.join(info_parts)}]")

        # Add conversation context if available
        if conversation_context and len(self.conversation_state.conversation_history) > 0:
            prompt_parts.append(f"[Previous conversation context:\n{conversation_context}]")

        # Add current input
        prompt_parts.append(f"Current user input: {input_data}")

        # Add instruction for context usage
        if prompt_parts[:-1]:  # If we have context
            prompt_parts.append(
                "\nPlease respond naturally, using the context above to personalize your response and maintain conversation continuity."
            )

        return "\n".join(prompt_parts)

    def _enhance_prompt_with_context(self, original_prompt: str) -> str:
        """Enhance any prompt with available context"""

        user_context = self.conversation_state.get_user_context()

        context_parts = []

        # Add user information
        if user_context.get("user_info"):
            context_parts.append(f"User context: {user_context['user_info']}")

        # Add conversation summary
        if user_context.get("conversation_summary"):
            context_parts.append(f"Conversation: {user_context['conversation_summary']}")

        if context_parts:
            enhanced_prompt = f"{original_prompt}\n\n[Context: {'; '.join(context_parts)}]"
            return enhanced_prompt

    def _build_memory_enhanced_prompt(self, input_data: str, memory_context: dict) -> str:
        """Build a prompt enhanced with memory system context"""

        prompt_parts = []

        # Add memory context if available
        if memory_context.get("context"):
            memory_items = memory_context["context"]
            if memory_items:
                prompt_parts.append("[Memory Context]")

                # Group memories by type for better organization
                memories_by_type = {}
                for item in memory_items:
                    if hasattr(item, "metadata") and hasattr(item.metadata, "type"):
                        mem_type = item.metadata.type.value
                        if mem_type not in memories_by_type:
                            memories_by_type[mem_type] = []
                        memories_by_type[mem_type].append(item.memory)

                # Add organized memory context
                for mem_type, memories in memories_by_type.items():
                    if memories:
                        prompt_parts.append(f"{mem_type.capitalize()}: {'; '.join(memories)}")

        # Add current input
        prompt_parts.append(f"Current user input: {input_data}")

        # Add instruction for memory usage
        if memory_context.get("context"):
            prompt_parts.append(
                "\nPlease respond naturally, using the memory context above to provide personalized and contextually relevant responses."
            )

        return "\n".join(prompt_parts)

    def _build_persistent_context_prompt(self, input_data: str, memory_context: dict) -> str:
        """Build a prompt with persistent cross-session context for Phase 3"""

        prompt_parts = []

        # Add cross-session context indicator
        if self.conversation_state.extracted_facts.get("session_restored"):
            restored_count = self.conversation_state.extracted_facts.get("restored_memories", 0)
            prompt_parts.append(f"[Cross-Session Context: Restored {restored_count} memories from previous sessions]")

        # Add organized memory context
        if memory_context.get("context"):
            memory_items = memory_context["context"]
            if memory_items:
                prompt_parts.append("[Persistent Memory Context]")

                # Group memories by type for better organization
                memories_by_type = {}
                for item in memory_items:
                    if hasattr(item, "metadata") and hasattr(item.metadata, "type"):
                        mem_type = item.metadata.type.value
                        if mem_type not in memories_by_type:
                            memories_by_type[mem_type] = []
                        memories_by_type[mem_type].append(item.memory)

                # Prioritize user information for cross-session continuity
                if "FACT" in memories_by_type:
                    prompt_parts.append(f"User Facts: {'; '.join(memories_by_type['FACT'])}")
                if "OPINION" in memories_by_type:
                    prompt_parts.append(f"User Preferences: {'; '.join(memories_by_type['OPINION'])}")
                if "PROCEDURE" in memories_by_type:
                    prompt_parts.append(f"User Procedures: {'; '.join(memories_by_type['PROCEDURE'])}")
                if "EVENT" in memories_by_type:
                    prompt_parts.append(f"User Events: {'; '.join(memories_by_type['EVENT'])}")
                if "TOPIC" in memories_by_type:
                    prompt_parts.append(f"Discussion Topics: {'; '.join(memories_by_type['TOPIC'])}")

        # Add current input
        prompt_parts.append(f"Current user input: {input_data}")

        # Add Phase 3 specific instruction
        if memory_context.get("context"):
            prompt_parts.append("""
Please respond naturally using the persistent memory context above. This context comes from previous sessions and conversations. Reference relevant information naturally, as if you remember our ongoing relationship and previous discussions. Use phrases like "As we discussed before..." or "Building on your previous work..." when appropriate.""")

        return "\n".join(prompt_parts)

    def _build_memory_context_summary(self, memory_context: dict) -> str:
        """Build a concise memory context summary for injection into agent context"""
        if not memory_context.get("context"):
            return ""

        memory_items = memory_context["context"]
        if not memory_items:
            return ""

        # Create a concise summary of recent memories
        summaries = []
        for item in memory_items[-3:]:  # Use last 3 memory items
            # Extract key information from the memory
            if hasattr(item, "memory") and item.memory:
                # Shorten long memories for context injection
                memory_text = item.memory
                if len(memory_text) > 200:
                    memory_text = memory_text[:200] + "..."
                summaries.append(memory_text)

        return "\n".join(summaries)

    def _build_memory_enhanced_input(self, input_data: str) -> str:
        """Build memory-enhanced input by prepending memory context to the original input"""
        try:
            if not self._memory_manager:
                return input_data

            # Get memory context
            memory_context = self._get_comprehensive_memory_context()

            if not memory_context:
                return input_data

            # Build enhanced input with memory context
            enhanced_input = f"""[Memory Context]
{memory_context}

[Current Query]
{input_data}

Please use the memory context above to provide a response that acknowledges our conversation history and any relevant information about the user."""

            return enhanced_input

        except Exception as e:
            print(f"Failed to build memory-enhanced input: {e}")
            return input_data

    def _get_comprehensive_memory_context(self) -> str:
        """Get comprehensive memory context as formatted text"""
        try:
            context_parts = []

            # Get working memory (recent conversations)
            working_memories = self._run_async_safely(self._memory_manager.working_memory.search([], limit=10))

            if working_memories:
                recent_conversations = self._extract_conversations_from_memories(working_memories)
                if recent_conversations:
                    context_parts.append("Recent Conversation History:")
                    for conv in recent_conversations[-3:]:  # Last 3 conversations
                        context_parts.append(f"User: {conv['user']}")
                        if conv["agent"]:
                            # Limit agent response length for context
                            agent_response = conv["agent"][:200] + "..." if len(conv["agent"]) > 200 else conv["agent"]
                            context_parts.append(f"Agent: {agent_response}")
                        context_parts.append("")

            # Get user facts from user memory
            if hasattr(self._memory_manager, "user_memory"):
                user_memories = self._run_async_safely(self._memory_manager.user_memory.search([], limit=20))
                if user_memories:
                    user_facts = self._extract_user_facts_from_memories(user_memories)
                    if user_facts:
                        context_parts.append("Known User Information:")
                        for fact in user_facts[:5]:  # Limit to 5 facts
                            context_parts.append(f"- {fact}")
                        context_parts.append("")

            # Add session info
            context_parts.append(f"Session: {self._memory_manager.session_id}")
            context_parts.append(f"User: {self._memory_manager.user_id}")

            return "\n".join(context_parts).strip()

        except Exception as e:
            print(f"Error getting memory context: {e}")
            return ""

    def _extract_conversations_from_memories(self, memories) -> list:
        """Extract conversation pairs from memory items"""
        conversations = []
        for memory in memories[-5:]:  # Last 5 memories
            if hasattr(memory, "memory") and memory.memory:
                # Parse User: and Agent: parts
                lines = memory.memory.split("\n")
                user_part = ""
                agent_part = ""

                current_speaker = None
                current_text = []

                for line in lines:
                    line = line.strip()
                    if line.startswith("User:"):
                        # Save previous agent text if any
                        if current_speaker == "Agent" and current_text:
                            agent_part = " ".join(current_text)

                        # Start new user text
                        current_speaker = "User"
                        user_part = line[5:].strip()
                        current_text = []

                    elif line.startswith("Agent:"):
                        # Start new agent text
                        current_speaker = "Agent"
                        current_text = [line[6:].strip()]

                    elif current_speaker == "Agent" and line:
                        # Continue agent text
                        current_text.append(line)

                # Save final agent text
                if current_speaker == "Agent" and current_text:
                    agent_part = " ".join(current_text)

                if user_part:
                    conversations.append(
                        {
                            "user": user_part,
                            "agent": agent_part,
                            "timestamp": memory.timestamp.isoformat() if hasattr(memory, "timestamp") else "unknown",
                        }
                    )

        return conversations

    def _extract_user_facts_from_memories(self, memories) -> list:
        """Extract user facts from memory items"""
        facts = []
        for memory in memories:
            if hasattr(memory, "memory") and memory.memory:
                content = memory.memory
                # Simple heuristic: look for personal information patterns
                if any(keyword in content.lower() for keyword in ["name is", "i am", "i work", "i like", "my favorite", "i prefer"]):
                    facts.append(content)
        return facts

    def _build_direct_memory_context(self, memory_items: list) -> str:
        """Build memory context summary directly from memory items"""
        if not memory_items:
            return ""

        summaries = []
        for item in memory_items[-3:]:  # Use last 3 memory items
            if hasattr(item, "memory") and item.memory:
                # Extract just the relevant conversation part
                memory_text = item.memory
                if len(memory_text) > 300:
                    memory_text = memory_text[:300] + "..."
                summaries.append(memory_text)

        return "\n---\n".join(summaries)

    def _run_async_safely(self, coro):
        """Run async coroutine safely in sync context using Dana's standard utility"""
        from dana.common.utils.misc import Misc

        # Use Dana's robust async handling that works across all environments
        return Misc.safe_asyncio_run(lambda: coro)

    def get_context_info(self) -> dict[str, Any]:
        """Get current context information (for debugging)"""
        info = {
            "session_id": self.conversation_state.session_id,
            "user_id": self.conversation_state.user_id,
            "agent_id": self.conversation_state.agent_id,
            "interaction_count": self.conversation_state.interaction_count,
            "extracted_facts": self.conversation_state.extracted_facts,
            "conversation_turns": len(self.conversation_state.conversation_history),
            "last_interaction": self.conversation_state.last_interaction.isoformat() if self.conversation_state.last_interaction else None,
            "memory_manager_available": self._memory_manager is not None,
        }

        # Add memory system info if available
        if self._memory_manager:
            info["memory_system"] = {
                "name": self._memory_manager.name,
                "use_llamaindex": getattr(self._memory_manager, "use_llamaindex", False),
                "use_json_storage": getattr(self._memory_manager, "use_json_storage", False),
                "storage_path": getattr(self._memory_manager, "storage_path", "unknown"),
            }

        # Add Phase 3 persistence info
        info["cross_session_persistence"] = {
            "enabled": self._memory_manager is not None,
            "session_restored": self.conversation_state.extracted_facts.get("session_restored", False),
            "restored_memories": self.conversation_state.extracted_facts.get("restored_memories", 0),
        }

        return info

    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation for debugging"""
        if not self.conversation_state.conversation_history:
            return "No conversation history"

        summary_parts = []
        summary_parts.append(f"Session: {self.conversation_state.session_id}")
        summary_parts.append(f"Interactions: {self.conversation_state.interaction_count}")

        if self.conversation_state.extracted_facts:
            summary_parts.append(f"User info: {self.conversation_state.extracted_facts}")

        recent_turns = self.conversation_state.get_recent_history(3)
        if recent_turns:
            summary_parts.append("Recent conversation:")
            for turn in recent_turns:
                summary_parts.append(f"  User: {turn.user_input}")
                summary_parts.append(f"  Agent: {turn.agent_response}")

        return "\n".join(summary_parts)

    def get_persistence_status(self) -> dict[str, Any]:
        """Get Phase 3 persistence status information"""
        status = {
            "cross_session_enabled": self._memory_manager is not None,
            "session_restored": self.conversation_state.extracted_facts.get("session_restored", False),
            "restored_memories": self.conversation_state.extracted_facts.get("restored_memories", 0),
            "user_id": self.conversation_state.user_id,
            "session_id": self.conversation_state.session_id,
            "storage_path": getattr(self._memory_manager, "storage_path", "unknown") if self._memory_manager else "no memory system",
        }

        # Add memory statistics if available
        if self._memory_manager:
            try:
                memory_stats = self._run_async_safely(self._memory_manager.get_memory_statistics())
                status["memory_statistics"] = memory_stats
            except Exception as e:
                status["memory_statistics"] = f"Error getting stats: {e}"

        return status

    def reset_context(self):
        """Reset context for testing"""
        self.conversation_state.clear_session()

    def __str__(self):
        return f"AgentContextManager(agent={self.conversation_state.agent_id}, session={self.conversation_state.session_id[:8]}...)"

    def __repr__(self):
        return self.__str__()
