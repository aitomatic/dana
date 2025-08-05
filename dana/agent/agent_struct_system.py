"""
Agent Struct System for Dana Language (Unified with Struct System)

This module implements agent capabilities by extending the struct system.
AgentStructType inherits from StructType, and AgentStructInstance inherits from StructInstance.

Design Reference: dana/agent/.design/3d_methodology_agent_struct_unification.md
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from dana.core.lang.interpreter.struct_system import StructInstance, StructType
from dana.core.lang.sandbox_context import SandboxContext

# --- Default Agent Method Implementations ---


def default_plan_method(agent_instance: "AgentStructInstance", task: str, user_context: dict | None = None) -> Any:
    """Default plan method for agent structs."""
    agent_fields = ", ".join(f"{k}: {v}" for k, v in agent_instance.__dict__.items() if not k.startswith("_"))
    # TODO: Implement actual planning logic with prompt
    # context_info = f" with context: {user_context}" if user_context else ""
    # prompt = f"""You are an agent with fields: {agent_fields}.
    #
    # Task: {task}{context_info}
    #
    # Please create a detailed plan for accomplishing this task. Consider the agent's capabilities and context.
    #
    # Return a structured plan with clear steps."""

    # For now, return a simple response since we don't have context access
    return f"Agent {agent_instance.agent_type.name} planning: {task} (fields: {agent_fields})"


def default_solve_method(agent_instance: "AgentStructInstance", problem: str, user_context: dict | None = None) -> Any:
    """Default solve method for agent structs."""
    agent_fields = ", ".join(f"{k}: {v}" for k, v in agent_instance.__dict__.items() if not k.startswith("_"))
    # TODO: Implement actual solving logic with prompt
    # context_info = f" with context: {user_context}" if user_context else ""
    # prompt = f"""You are an agent with fields: {agent_fields}.
    #
    # Problem: {problem}{context_info}
    #
    # Please provide a solution to this problem. Use the agent's capabilities and context to formulate an effective response.
    #
    # Return a comprehensive solution."""

    # For now, return a simple response since we don't have context access
    return f"Agent {agent_instance.agent_type.name} solving: {problem} (fields: {agent_fields})"


def default_remember_method(agent_instance: "AgentStructInstance", key: str, value: Any) -> bool:
    """Default remember method for agent structs."""
    # Initialize memory if it doesn't exist
    try:
        agent_instance._memory[key] = value
    except AttributeError:
        # Memory not initialized yet, create it
        agent_instance._memory = {key: value}
    return True


def default_recall_method(agent_instance: "AgentStructInstance", key: str) -> Any:
    """Default recall method for agent structs."""
    # Use try/except instead of hasattr to avoid sandbox restrictions
    try:
        return agent_instance._memory.get(key, None)
    except AttributeError:
        # Memory not initialized yet
        return None


def default_chat_method(
    agent_instance: "AgentStructInstance", message: str, context: dict | None = None, max_context_turns: int = 5
) -> str:
    """Default chat method for agent structs - delegates to instance method."""
    return agent_instance._chat_impl(message, context, max_context_turns)


# --- Agent Struct Type System ---


@dataclass
class AgentStructType(StructType):
    """Agent struct type with built-in agent capabilities.

    Inherits from StructType and adds agent-specific functionality.
    """

    # Agent-specific capabilities
    agent_methods: dict[str, Callable] = field(default_factory=dict)
    memory_system: Any | None = None  # Placeholder for future memory system
    reasoning_capabilities: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default agent methods."""
        super().__post_init__()

        # Add default agent methods
        self.agent_methods.update(
            {
                "plan": default_plan_method,
                "solve": default_solve_method,
                "remember": default_remember_method,
                "recall": default_recall_method,
                "chat": default_chat_method,
            }
        )

    def add_agent_method(self, name: str, method: Callable):
        """Add agent-specific method."""
        self.agent_methods[name] = method

    def has_agent_method(self, name: str) -> bool:
        """Check if agent has a specific method."""
        return name in self.agent_methods


class AgentStructInstance(StructInstance):
    """Agent struct instance with built-in agent capabilities.

    Inherits from StructInstance and adds agent-specific state and methods.
    """

    def __init__(self, struct_type: AgentStructType, values: dict[str, Any]):
        """Create a new agent struct instance.

        Args:
            struct_type: The agent struct type definition
            values: Field values (must match struct type requirements)
        """
        # Ensure we have an AgentStructType
        if not isinstance(struct_type, AgentStructType):
            raise TypeError(f"AgentStructInstance requires AgentStructType, got {type(struct_type)}")

        # Initialize the base StructInstance
        super().__init__(struct_type, values)

        # Initialize agent-specific state
        self._memory = {}
        self._context = {}
        self._conversation_memory = None  # Lazy initialization
        self._llm_resource = None  # Lazy initialization

    @property
    def agent_type(self) -> AgentStructType:
        """Get the agent type."""
        return self.__struct_type__

    def plan(self, task: str, context: dict | None = None) -> Any:
        """Execute agent planning method."""
        if self.__struct_type__.has_agent_method("plan"):
            return self.__struct_type__.agent_methods["plan"](self, task, context)
        return default_plan_method(self, task, context)

    def solve(self, problem: str, context: dict | None = None) -> Any:
        """Execute agent problem-solving method."""
        if self.__struct_type__.has_agent_method("solve"):
            return self.__struct_type__.agent_methods["solve"](self, problem, context)
        return default_solve_method(self, problem, context)

    def remember(self, key: str, value: Any) -> bool:
        """Store information in agent memory."""
        if self.__struct_type__.has_agent_method("remember"):
            return self.__struct_type__.agent_methods["remember"](self, key, value)
        return default_remember_method(self, key, value)

    def recall(self, key: str) -> Any:
        """Retrieve information from agent memory."""
        if self.__struct_type__.has_agent_method("recall"):
            return self.__struct_type__.agent_methods["recall"](self, key)
        return default_recall_method(self, key)

    def chat(self, message: str, context: dict | None = None, max_context_turns: int = 5) -> str:
        """Chat with the agent using conversation memory."""
        if self.__struct_type__.has_agent_method("chat"):
            return self.__struct_type__.agent_methods["chat"](self, message, context, max_context_turns)
        return default_chat_method(self, message, context, max_context_turns)

    def _initialize_conversation_memory(self):
        """Initialize conversation memory if not already done."""
        if self._conversation_memory is None:
            from pathlib import Path

            from dana.frameworks.memory.conversation_memory import ConversationMemory

            # Create memory file path under ~/.dana/chats/
            agent_name = getattr(self.agent_type, "name", "agent")
            home_dir = Path.home()
            dana_dir = home_dir / ".dana"
            memory_dir = dana_dir / "chats"
            memory_dir.mkdir(parents=True, exist_ok=True)
            memory_file = memory_dir / f"{agent_name}_conversation.json"

            self._conversation_memory = ConversationMemory(
                filepath=str(memory_file),
                max_turns=20,  # Keep last 20 turns in active memory
            )

    def _get_llm_function(self):
        """Get LLM function from agent fields, context, or Dana's stdlib llm_function."""
        # Check if agent has an llm field
        if hasattr(self, "llm") and callable(self.llm):
            return self.llm

        # Check agent's context
        if "llm" in self._context and callable(self._context["llm"]):
            return self._context["llm"]

        # Use Dana's stdlib llm_function
        return self._get_dana_llm_function()

    def _get_dana_llm_function(self):
        """Get Dana's stdlib llm_function with sandbox context."""
        try:
            from dana.core.lang.sandbox_context import SandboxContext
            from dana.core.stdlib.core.llm_function import llm_function

            # Create a minimal sandbox context for LLM calls
            # In a real Dana execution environment, this would be provided
            # For now, create a minimal context
            context = SandboxContext()

            # Create a wrapper that uses Dana's llm_function
            def wrapped_llm_function(prompt: str) -> str:
                try:
                    # Call Dana's llm_function which returns a Promise
                    promise = llm_function(context, prompt)

                    # Properly resolve the Promise to get the actual content
                    if hasattr(promise, "_ensure_resolved"):
                        # For EagerPromise, use _ensure_resolved to get the actual value
                        result = promise._ensure_resolved()
                    elif hasattr(promise, "resolve"):
                        # Fallback for other Promise types
                        result = promise.resolve()
                    else:
                        # If it's not a Promise, return as-is
                        result = promise

                    return str(result) if result is not None else "No response from LLM"

                except Exception as e:
                    return f"LLM call failed: {str(e)}"

            return wrapped_llm_function

        except Exception:
            # If Dana's llm_function is not available, return None for fallback
            return None

    def _build_agent_description(self) -> str:
        """Build a description of the agent for LLM prompts."""
        description = f"You are {self.agent_type.name}."

        # Add agent fields to description from _values
        if hasattr(self, "_values") and self._values:
            agent_fields = []
            for field_name, field_value in self._values.items():
                agent_fields.append(f"{field_name}: {field_value}")

            if agent_fields:
                description += f" Your characteristics: {', '.join(agent_fields)}."

        return description

    def _generate_fallback_response(self, message: str, context: str) -> str:
        """Generate a fallback response when LLM is not available."""
        message_lower = message.lower()

        # Check for greetings
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "greetings"]):
            return f"Hello! I'm {self.agent_type.name}. How can I help you today?"

        # Check for name queries
        if "your name" in message_lower or "who are you" in message_lower:
            return f"I'm {self.agent_type.name}, an AI agent. How can I assist you?"

        # Check for memory-related queries
        if "remember" in message_lower or "recall" in message_lower:
            recent_turns = self._conversation_memory.get_recent_context(3)
            if recent_turns:
                topics = []
                for turn in recent_turns:
                    words = turn["user_input"].split()
                    topics.extend([w for w in words if len(w) > 4])
                if topics:
                    unique_topics = list(set(topics))[:3]
                    return f"I remember we discussed: {', '.join(unique_topics)}"
            return "We haven't discussed much yet in this conversation."

        # Check for help queries
        if "help" in message_lower or "what can you do" in message_lower:
            return (
                f"I'm {self.agent_type.name}. I can chat with you and remember our "
                "conversation. I'll provide better responses when connected to an LLM."
            )

        # Default response
        return (
            f"I understand you said: '{message}'. As {self.agent_type.name}, "
            "I'm currently running without an LLM connection, so my responses are limited."
        )

    def _chat_impl(self, message: str, context: dict | None = None, max_context_turns: int = 5) -> str:
        """Implementation of chat functionality."""
        # Initialize conversation memory if needed
        self._initialize_conversation_memory()

        # Build conversation context
        conversation_context = self._conversation_memory.build_llm_context(message, include_summaries=True, max_turns=max_context_turns)

        # Try to get LLM function
        llm_function = self._get_llm_function()

        if llm_function:
            # Build prompt with agent description and conversation context
            system_prompt = self._build_agent_description()

            # Add any additional context
            if context:
                system_prompt += f" Additional context: {context}"

            # Combine system prompt with conversation context
            full_prompt = f"{system_prompt}\n\n{conversation_context}"

            # Call LLM to generate response
            try:
                response = llm_function(full_prompt)
            except Exception as e:
                response = f"I encountered an error while processing your message: {str(e)}"
        else:
            # Use fallback response when no LLM is available
            response = self._generate_fallback_response(message, conversation_context)

        # Save the conversation turn
        self._conversation_memory.add_turn(message, response)

        return response

    def get_conversation_stats(self) -> dict:
        """Get conversation statistics for this agent."""
        if self._conversation_memory is None:
            return {"error": "Conversation memory not initialized"}
        return self._conversation_memory.get_statistics()

    def clear_conversation_memory(self) -> bool:
        """Clear the conversation memory for this agent."""
        if self._conversation_memory is None:
            return False
        self._conversation_memory.clear()
        return True


# --- Agent Type Registry ---


class AgentStructTypeRegistry:
    """Registry for agent struct types.

    Extends the existing StructTypeRegistry to handle agent types.
    """

    def __init__(self):
        self._agent_types: dict[str, AgentStructType] = {}

    def register_agent_type(self, agent_type: AgentStructType) -> None:
        """Register an agent struct type."""
        self._agent_types[agent_type.name] = agent_type

    def get_agent_type(self, name: str) -> AgentStructType | None:
        """Get an agent struct type by name."""
        return self._agent_types.get(name)

    def list_agent_types(self) -> list[str]:
        """List all registered agent type names."""
        return list(self._agent_types.keys())

    def create_agent_instance(self, name: str, field_values: dict[str, Any], context: SandboxContext) -> AgentStructInstance:
        """Create an agent struct instance."""
        agent_type = self.get_agent_type(name)
        if not agent_type:
            raise ValueError(f"Unknown agent type: {name}")

        # Create instance with field values
        instance = AgentStructInstance(agent_type, field_values)

        return instance


# --- Global Registry Instance ---

# Global registry for agent struct types
agent_struct_type_registry = AgentStructTypeRegistry()


# --- Utility Functions ---


def register_agent_struct_type(agent_type: AgentStructType) -> None:
    """Register an agent struct type in the global registry."""
    agent_struct_type_registry.register_agent_type(agent_type)

    # Also register in the struct registry so method dispatch can find it
    from dana.core.lang.interpreter.struct_system import StructTypeRegistry

    StructTypeRegistry.register(agent_type)


def get_agent_struct_type(name: str) -> AgentStructType | None:
    """Get an agent struct type from the global registry."""
    return agent_struct_type_registry.get_agent_type(name)


def create_agent_struct_instance(name: str, field_values: dict[str, Any], context: SandboxContext) -> AgentStructInstance:
    """Create an agent struct instance using the global registry."""
    return agent_struct_type_registry.create_agent_instance(name, field_values, context)
