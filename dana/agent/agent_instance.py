"""
Agent Struct System for Dana Language (Unified with Struct System)

This module implements agent capabilities by extending the struct system.
AgentStructType inherits from StructType, and AgentStructInstance inherits from StructInstance.

Design Reference: dana/agent/.design/3d_methodology_base_agent_unification.md
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.core.concurrency.promise_factory import PromiseFactory
from dana.core.lang.interpreter.struct_system import StructInstance, StructType, universal_dana_method_registry
from dana.core.lang.sandbox_context import SandboxContext

# --- Default Agent Method Implementations ---


def default_plan_method(
    agent_instance: "AgentInstance", sandbox_context: SandboxContext, task: str, user_context: dict | None = None
) -> Any:
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


def default_solve_method(
    agent_instance: "AgentInstance", sandbox_context: SandboxContext, problem: str, user_context: dict | None = None
) -> Any:
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


def default_remember_method(agent_instance: "AgentInstance", sandbox_context: SandboxContext, key: str, value: Any) -> bool:
    """Default remember method for agent structs."""
    # Initialize memory if it doesn't exist
    try:
        agent_instance._memory[key] = value
    except AttributeError:
        # Memory not initialized yet, create it
        agent_instance._memory = {key: value}
    return True


def default_recall_method(agent_instance: "AgentInstance", sandbox_context: SandboxContext, key: str) -> Any:
    """Default recall method for agent structs."""
    # Use try/except instead of hasattr to avoid sandbox restrictions
    try:
        return agent_instance._memory.get(key, None)
    except AttributeError:
        # Memory not initialized yet
        return None


def default_reason_method(
    agent_instance: "AgentInstance", sandbox_context: SandboxContext, premise: str, context: dict | None = None
) -> Any:
    """Default reason method for agent structs."""
    agent_fields = ", ".join(f"{k}: {v}" for k, v in agent_instance.__dict__.items() if not k.startswith("_"))
    # TODO: Implement actual reasoning logic with prompt
    # context_info = f" with context: {context}" if context else ""
    # prompt = f"""You are an agent with fields: {agent_fields}.
    #
    # Premise: {premise}{context_info}
    #
    # Please reason about this premise. Apply logical thinking, consider implications,
    # and draw reasonable conclusions based on the available information.
    #
    # Return your reasoning process and conclusions."""

    # For now, return a simple response since we don't have context access
    return f"Agent {agent_instance.agent_type.name} reasoning about: {premise} (fields: {agent_fields})"


def default_chat_method(
    agent_instance: "AgentInstance",
    sandbox_context: SandboxContext,
    message: str,
    context: dict | None = None,
    max_context_turns: int = 5,
) -> Any:
    """Default chat method for agent structs - delegates to instance method."""
    return agent_instance._chat_impl(sandbox_context, message, context, max_context_turns)


# --- Agent Struct Type System ---


@dataclass
class AgentType(StructType):
    """Agent struct type with built-in agent capabilities.

    Inherits from StructType and adds agent-specific functionality.
    """

    # Agent-specific capabilities
    memory_system: Any | None = None  # Placeholder for future memory system
    reasoning_capabilities: list[str] = field(default_factory=list)

    def __init__(
        self,
        name: str,
        fields: dict[str, str],
        field_order: list[str],
        field_comments: dict[str, str] | None = None,
        field_defaults: dict[str, Any] | None = None,
        docstring: str | None = None,
        memory_system: Any | None = None,
        reasoning_capabilities: list[str] | None = None,
        agent_methods: dict[str, Callable] | None = None,
    ):
        """Initialize AgentType with support for agent_methods parameter."""
        # Set agent-specific attributes FIRST
        self.memory_system = memory_system
        self.reasoning_capabilities = reasoning_capabilities or []

        # Store agent_methods temporarily just for __post_init__ registration
        # This is not stored as persistent instance state since the universal registry
        # is the single source of truth for agent methods
        self._temp_agent_methods = agent_methods or {}

        # Initialize as a regular StructType first
        super().__init__(
            name=name,
            fields=fields,
            field_order=field_order,
            field_comments=field_comments or {},
            field_defaults=field_defaults,
            docstring=docstring,
        )

    def __post_init__(self):
        """Initialize agent methods and add default agent fields."""
        # Add default agent fields automatically
        additional_fields = AgentInstance.get_default_agent_fields()
        self.merge_additional_fields(additional_fields)

        # Register default agent methods (defined by AgentInstance)
        default_methods = AgentInstance.get_default_dana_methods()
        for method_name, method in default_methods.items():
            universal_dana_method_registry.register_method(self.name, method_name, method)

        # Register any custom agent methods that were passed in during initialization
        for method_name, method in self._temp_agent_methods.items():
            universal_dana_method_registry.register_method(self.name, method_name, method)

        # Clean up temporary storage since the registry is now the source of truth
        del self._temp_agent_methods

        # Call parent's post-init last
        super().__post_init__()

    def add_agent_method(self, name: str, method: Callable) -> None:
        """Add an agent-specific method to the universal registry."""
        universal_dana_method_registry.register_method(self.name, name, method)

    def has_agent_method(self, name: str) -> bool:
        """Check if this agent type has a specific method."""
        return universal_dana_method_registry.has_method(self.name, name)

    def get_agent_method(self, name: str) -> Callable | None:
        """Get an agent method by name."""
        return universal_dana_method_registry.lookup_method(self.name, name)

    @property
    def agent_methods(self) -> dict[str, Callable]:
        """Get all agent methods for this type."""
        methods = {}
        # Get all methods registered for this agent type from the registry
        from dana.core.lang.interpreter.struct_system import TypeAwareMethodRegistry

        # Access the internal registry to find all methods for this agent type
        for (receiver_type, method_name), method in TypeAwareMethodRegistry._methods.items():
            if receiver_type == self.name:
                methods[method_name] = method

        return methods


class AgentInstance(StructInstance):
    """Agent struct instance with built-in agent capabilities.

    Inherits from StructInstance and adds agent-specific state and methods.
    """

    def __init__(self, struct_type: AgentType, values: dict[str, Any]):
        """Create a new agent struct instance.

        Args:
            struct_type: The agent struct type definition
            values: Field values (must match struct type requirements)
        """
        # Ensure we have an AgentStructType
        if not isinstance(struct_type, AgentType):
            raise TypeError(f"AgentStructInstance requires AgentStructType, got {type(struct_type)}")

        # Initialize the base StructInstance
        super().__init__(struct_type, values)

        # Initialize agent-specific state
        self._memory = {}
        self._context = {}
        self._conversation_memory = None  # Lazy initialization
        self._llm_resource: LegacyLLMResource = None  # Lazy initialization
        self._llm_resource_instance = None  # Lazy initialization

    @staticmethod
    def get_default_dana_methods() -> dict[str, Callable]:
        """Get the default agent methods that all agents should have.

        This method defines what the standard agent methods are,
        keeping the definition close to where they're implemented.
        """
        return {
            "plan": default_plan_method,
            "solve": default_solve_method,
            "remember": default_remember_method,
            "recall": default_recall_method,
            "reason": default_reason_method,
            "chat": default_chat_method,
        }

    @staticmethod
    def get_default_agent_fields() -> dict[str, str | dict[str, Any]]:
        """Get the default fields that all agents should have.

        This method defines what the standard agent fields are,
        keeping the definition close to where they're used.
        """
        return {
            "state": {
                "type": "str",
                "default": "CREATED",
                "comment": "Current state of the agent",
            }
        }

    @property
    def agent_type(self) -> AgentType:
        """Get the agent type."""
        return self.__struct_type__  # type: ignore

    def plan(self, sandbox_context: SandboxContext, task: str, context: dict | None = None) -> Any:
        """Execute agent planning method."""
        method = universal_dana_method_registry.lookup_method(self.__struct_type__.name, "plan")
        if method:
            return method(self, sandbox_context, task, context)
        return default_plan_method(self, sandbox_context, task, context)

    def solve(self, sandbox_context: SandboxContext, problem: str, context: dict | None = None) -> Any:
        """Execute agent problem-solving method."""
        method = universal_dana_method_registry.lookup_method(self.__struct_type__.name, "solve")
        if method:
            return method(self, sandbox_context, problem, context)
        return default_solve_method(self, sandbox_context, problem, context)

    def remember(self, sandbox_context: SandboxContext, key: str, value: Any) -> bool:
        """Execute agent memory storage method."""
        method = universal_dana_method_registry.lookup_method(self.__struct_type__.name, "remember")
        if method:
            return method(self, sandbox_context, key, value)
        return default_remember_method(self, sandbox_context, key, value)

    def recall(self, sandbox_context: SandboxContext, key: str) -> Any:
        """Execute agent memory retrieval method."""
        method = universal_dana_method_registry.lookup_method(self.__struct_type__.name, "recall")
        if method:
            return method(self, sandbox_context, key)
        return default_recall_method(self, sandbox_context, key)

    def reason(self, sandbox_context: SandboxContext, premise: str, context: dict | None = None) -> Any:
        """Execute agent reasoning method."""
        method = universal_dana_method_registry.lookup_method(self.__struct_type__.name, "reason")
        if method:
            return method(self, sandbox_context, premise, context)
        return default_reason_method(self, sandbox_context, premise, context)

    def chat(self, sandbox_context: SandboxContext, message: str, context: dict | None = None, max_context_turns: int = 5) -> Any:
        """Execute agent chat method."""
        method = universal_dana_method_registry.lookup_method(self.__struct_type__.name, "chat")
        if method:
            return method(self, sandbox_context, message, context, max_context_turns)
        return default_chat_method(self, sandbox_context, message, context, max_context_turns)

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

    def _initialize_llm_resource(self):
        """Initialize LLM resource from agent's config if not already done."""
        if self._llm_resource_instance is None:
            from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
            from dana.core.resource.builtins.llm_resource_type import LLMResourceType

            # Get LLM parameters from agent's config field
            llm_params = {}
            if hasattr(self, "_values") and "config" in self._values:
                config = self._values["config"]
                if isinstance(config, dict):
                    # Extract LLM parameters from config
                    llm_params = {
                        "model": config.get("llm_model", config.get("model", "auto")),
                        "temperature": config.get("llm_temperature", config.get("temperature", 0.7)),
                        "max_tokens": config.get("llm_max_tokens", config.get("max_tokens", 2048)),
                        "provider": config.get("llm_provider", config.get("provider", "auto")),
                    }
                    # Add any other LLM-related config keys
                    for key, value in config.items():
                        if key.startswith("llm_") and key not in ["llm_model", "llm_temperature", "llm_max_tokens", "llm_provider"]:
                            llm_params[key[4:]] = value  # Remove "llm_" prefix

            # Create the underlying LLM resource
            self._llm_resource = LegacyLLMResource(
                name=f"{self.agent_type.name}_llm",
                model=llm_params.get("model", "auto"),
                temperature=llm_params.get("temperature", 0.7),
                max_tokens=llm_params.get("max_tokens", 2048),
                **{k: v for k, v in llm_params.items() if k not in ["model", "temperature", "max_tokens"]},
            )

            print(f"CTN >>> LLM resource: {self._llm_resource}")

            # Create the LLM resource instance
            self._llm_resource_instance = LLMResourceType.create_instance(
                self._llm_resource,
                values={
                    "name": f"{self.agent_type.name}_llm",
                    "model": llm_params.get("model", "auto"),
                    "provider": llm_params.get("provider", "auto"),
                    "temperature": llm_params.get("temperature", 0.7),
                    "max_tokens": llm_params.get("max_tokens", 2048),
                },
            )

            # Initialize the resource
            self._llm_resource_instance.initialize()
            self._llm_resource_instance.start()

    def _get_llm_resource(self, sandbox_context: SandboxContext | None = None):
        """Get LLM resource - prioritize agent's own LLM resource, fallback to sandbox context."""
        try:
            # First, try to use the agent's own LLM resource
            if self._llm_resource_instance is None:
                self._initialize_llm_resource()
                print(f"CTN >>> Initialized agent's own LLM resource: {self._llm_resource_instance}")

            if self._llm_resource_instance and self._llm_resource_instance.is_available:
                print(f"CTN >>> Using agent's own LLM resource: {self._llm_resource_instance}")
                return self._llm_resource_instance

            # Fallback to sandbox context if agent's LLM is not available
            if sandbox_context is not None:
                # Look for LLM resource in agent's available resources
                resources = sandbox_context.get_resources()
                for _, resource in resources.items():
                    if hasattr(resource, "kind") and resource.kind == "llm":
                        return resource
            return None
        except Exception:
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
            assert self._conversation_memory is not None  # Should be initialized by now
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

    def _create_response_promise(self, computation: Callable[[], Any], message: str) -> Any:
        """
        Create a Promise with conversation memory callback.

        Args:
            computation: Function that computes the response
            message: The original user message (for conversation memory)

        Returns:
            Promise that resolves to the response string
        """

        def save_conversation_callback(response: str):
            """Callback to save the conversation turn when the response is ready."""
            if self._conversation_memory:
                self._conversation_memory.add_turn(message, response)

        return PromiseFactory.create_promise(computation=computation, on_delivery=save_conversation_callback)

    def _chat_impl(
        self, sandbox_context: SandboxContext | None = None, message: str = "", context: dict | None = None, max_context_turns: int = 5
    ) -> Any:
        """Implementation of chat functionality. Returns a Promise that resolves to the response."""
        # Initialize conversation memory if needed
        self._initialize_conversation_memory()

        # Build conversation context
        assert self._conversation_memory is not None  # Should be initialized by _initialize_conversation_memory
        conversation_context = self._conversation_memory.build_llm_context(message, include_summaries=True, max_turns=max_context_turns)

        # Try to get LLM resource - prioritize agent's own LLM resource
        llm_resource = self._get_llm_resource(sandbox_context)

        # Fallback to sandbox context if agent's LLM is not available
        if llm_resource is None and sandbox_context is not None:
            # Look for LLM resource in agent's available resources
            resources = sandbox_context.get_resources()
            for _, resource in resources.items():
                if hasattr(resource, "kind") and resource.kind == "llm":
                    llm_resource = resource
                    break

        if llm_resource:
            # Build prompt with agent description and conversation context
            system_prompt = self._build_agent_description()

            # Add any additional context
            if context:
                system_prompt += f" Additional context: {context}"

            # Create computation that will call LLM resource through core resource interface
            def llm_computation():
                try:
                    from dana.common.types import BaseRequest

                    # Build proper messages format for LLM query
                    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]

                    # Add conversation context if available
                    if conversation_context.strip():
                        # Insert conversation context before the user message
                        messages.insert(-1, {"role": "system", "content": f"Previous conversation:\n{conversation_context}"})

                    # Use core resource interface
                    request = BaseRequest(arguments={"messages": messages})
                    response = llm_resource.query_sync(request)  # Use synchronous query

                    if response.success:
                        # Extract the actual text content from the response
                        content = response.content
                        if isinstance(content, dict):
                            if "choices" in content and content["choices"]:
                                # OpenAI/Anthropic style response
                                first_choice = content["choices"][0]
                                if isinstance(first_choice, dict) and "message" in first_choice:
                                    response_message = first_choice["message"]
                                    if isinstance(response_message, dict) and "content" in response_message:
                                        return response_message["content"]
                                    elif hasattr(response_message, "content"):
                                        return response_message.content
                                elif hasattr(first_choice, "message") and hasattr(first_choice.message, "content"):
                                    return first_choice.message.content
                            elif "content" in content:
                                return content["content"]
                            elif "response" in content:
                                return content["response"]
                        # If we can't extract content, return the whole response as string
                        return str(content)
                    else:
                        return f"LLM call failed: {response.error}"
                except Exception as e:
                    return f"I encountered an error while processing your message: {str(e)}"

            return self._create_response_promise(llm_computation, message)
        else:
            # For fallback response, execute synchronously but still use Promise for consistency
            def fallback_computation():
                return self._generate_fallback_response(message, conversation_context)

            return self._create_response_promise(fallback_computation, message)

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


class AgentTypeRegistry:
    """Registry for agent struct types.

    Extends the existing StructTypeRegistry to handle agent types.
    """

    def __init__(self):
        self._agent_types: dict[str, AgentType] = {}

    def register_agent_type(self, agent_type: AgentType) -> None:
        """Register an agent struct type."""
        self._agent_types[agent_type.name] = agent_type

    def get_agent_type(self, name: str) -> AgentType | None:
        """Get an agent struct type by name."""
        return self._agent_types.get(name)

    def list_agent_types(self) -> list[str]:
        """List all registered agent type names."""
        return list(self._agent_types.keys())

    def create_agent_instance(self, name: str, field_values: dict[str, Any], context: SandboxContext) -> AgentInstance:
        """Create an agent struct instance."""
        agent_type = self.get_agent_type(name)
        if not agent_type:
            raise ValueError(f"Unknown agent type: {name}")

        # Create instance with field values
        instance = AgentInstance(agent_type, field_values)

        return instance


# --- Global Registry Instance ---

# Global registry for agent struct types
agent_type_registry = AgentTypeRegistry()


# --- Utility Functions ---


def register_agent_type(agent_type: AgentType) -> None:
    """Register an agent struct type in the global registry."""
    agent_type_registry.register_agent_type(agent_type)

    # Also register in the struct registry so method dispatch can find it
    from dana.core.lang.interpreter.struct_system import StructTypeRegistry

    StructTypeRegistry.register(agent_type)


def get_agent_type(name: str) -> AgentType | None:
    """Get an agent struct type from the global registry."""
    return agent_type_registry.get_agent_type(name)


def create_agent_instance(name: str, field_values: dict[str, Any], context: SandboxContext) -> AgentInstance:
    """Create an agent struct instance using the global registry."""
    return agent_type_registry.create_agent_instance(name, field_values, context)
