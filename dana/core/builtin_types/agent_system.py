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
from dana.core.builtin_types.struct_system import StructInstance, StructType
from dana.core.builtin_types.resource.resource_instance import ResourceInstance
from dana.core.builtin_types.workflow_system import WorkflowInstance
from dana.core.concurrency.promise_factory import PromiseFactory
from dana.core.concurrency.promise_utils import is_promise
from dana.core.lang.sandbox_context import SandboxContext

# For backward compatibility, create aliases
from dana.registry import (
    get_agent_type,
)


# Create backward compatibility functions and instances
def create_agent_instance(agent_type_name: str, field_values=None, context=None):
    """Create an agent instance (backward compatibility)."""
    from dana.core.builtin_types.agent_system import AgentInstance

    agent_type = get_agent_type(agent_type_name)
    if agent_type is None:
        raise ValueError(f"Agent type '{agent_type_name}' not found")
    return AgentInstance(agent_type, field_values or {})


# Runtime function definitions
def lookup_dana_method(receiver_type: str, method_name: str):
    from dana.registry import FUNCTION_REGISTRY

    return FUNCTION_REGISTRY.lookup_struct_function(receiver_type, method_name)


def register_dana_method(receiver_type: str, method_name: str, func: Callable):
    from dana.registry import FUNCTION_REGISTRY

    return FUNCTION_REGISTRY.register_struct_function(receiver_type, method_name, func)


def has_dana_method(receiver_type: str, method_name: str):
    from dana.registry import FUNCTION_REGISTRY

    return FUNCTION_REGISTRY.has_struct_function(receiver_type, method_name)


# Avoid importing registries at module import time to prevent circular imports.
# Import needed registries lazily inside methods.

# --- Registry Integration ---
# Import the centralized registry from the new location

# Re-export for backward compatibility
__all__ = getattr(globals(), "__all__", [])
__all__.extend(
    [
        "AgentTypeRegistry",
        "global_agent_type_registry",
        "register_agent_type",
        "get_agent_type",
        "create_agent_instance",
    ]
)

# --- Default Agent Method Implementations ---


def default_plan_method(
    agent_instance: "AgentInstance", sandbox_context: SandboxContext, task: str, user_context: dict | None = None
) -> Any:
    """Default plan method for agent structs - delegates to instance method."""

    # Simply delegate to the built-in implementation
    # The main plan() method will handle Promise wrapping
    def wrapper():
        return agent_instance._plan_impl(sandbox_context, task, user_context)

    return PromiseFactory.create_promise(computation=wrapper)


def default_solve_method(
        agent_instance: "AgentInstance", sandbox_context: SandboxContext, problem: str, context: dict | None = None,
        resources: list[ResourceInstance] | None = None, workflows: list[WorkflowInstance] | None = None) -> Any:
    """Default solve method for agent structs - delegates to instance method."""

    # Simply delegate to the built-in implementation
    # The main solve() method will handle Promise wrapping
    def wrapper():
        return agent_instance._solve_impl(sandbox_context=sandbox_context,
                                          problem=problem,
                                          context=context,
                                          resources=resources,
                                          workflows=workflows)

    return PromiseFactory.create_promise(computation=wrapper)


def default_remember_method(agent_instance: "AgentInstance", sandbox_context: SandboxContext, key: str, value: Any) -> Any:
    """Default remember method for agent structs - delegates to instance method."""

    # Simply delegate to the built-in implementation
    # The main remember() method will handle Promise wrapping
    def wrapper():
        return agent_instance._remember_impl(sandbox_context, key, value)

    return PromiseFactory.create_promise(computation=wrapper)


def default_recall_method(agent_instance: "AgentInstance", sandbox_context: SandboxContext, key: str) -> Any:
    """Default recall method for agent structs - delegates to instance method."""

    # Simply delegate to the built-in implementation
    # The main recall() method will handle Promise wrapping
    def wrapper():
        return agent_instance._recall_impl(sandbox_context, key)

    return PromiseFactory.create_promise(computation=wrapper)


def default_reason_method(
        agent_instance: "AgentInstance", sandbox_context: SandboxContext, premise: str, context: dict | None = None,
        resources: list[ResourceInstance] | None = None) -> Any:
    """Default reason method for agent structs - delegates to instance method."""

    # Check if we have a type context that needs to be preserved
    current_assignment_type = sandbox_context.get("system:__current_assignment_type")

    # Simply delegate to the built-in implementation
    # The main reason() method will handle Promise wrapping
    def wrapper():
        # Ensure the type context is preserved in the sandbox context
        if current_assignment_type:
            sandbox_context.set("system:__current_assignment_type", current_assignment_type)
        return agent_instance._reason_impl(sandbox_context, premise, context)

    return PromiseFactory.create_promise(computation=wrapper)


def default_chat_method(
    agent_instance: "AgentInstance",
    sandbox_context: SandboxContext,
    message: str,
    context: dict | None = None,
    max_context_turns: int = 5,
) -> Any:
    """Default chat method for agent structs - delegates to instance method."""

    # Initialize conversation memory before creating the Promise
    agent_instance._initialize_conversation_memory()

    def wrapper():
        return agent_instance._chat_impl(sandbox_context, message, context, max_context_turns)

    def save_conversation_callback(response):
        """Callback to save the conversation turn when the response is ready."""
        if agent_instance._conversation_memory:
            # Handle case where response might be an EagerPromise
            if is_promise(response):
                response = response._wait_for_delivery()
            agent_instance._conversation_memory.add_turn(message, response)

    return PromiseFactory.create_promise(computation=wrapper, on_delivery=save_conversation_callback)


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
            register_dana_method(self.name, method_name, method)

        # Register any custom agent methods that were passed in during initialization
        for method_name, method in self._temp_agent_methods.items():
            register_dana_method(self.name, method_name, method)

        # Clean up temporary storage since the registry is now the source of truth
        del self._temp_agent_methods

        # Call parent's post-init last
        super().__post_init__()

    def add_agent_method(self, name: str, method: Callable) -> None:
        """Add an agent-specific method to the universal registry."""
        register_dana_method(self.name, name, method)

    def has_agent_method(self, name: str) -> bool:
        """Check if this agent type has a specific method."""
        return has_dana_method(self.name, name)

    def get_agent_method(self, name: str) -> Callable | None:
        """Get an agent method by name."""
        return lookup_dana_method(self.name, name)

    @property
    def agent_methods(self) -> dict[str, Callable]:
        """Get all agent methods for this type."""
        from dana.registry import FUNCTION_REGISTRY

        methods = {}

        # First, check the internal struct methods storage
        for (receiver_type, method_name), (method, _) in FUNCTION_REGISTRY._struct_functions.items():
            if receiver_type == self.name:
                methods[method_name] = method

        # Then, check the delegated StructFunctionRegistry if it exists
        if FUNCTION_REGISTRY._struct_function_registry is not None:
            delegated_registry = FUNCTION_REGISTRY._struct_function_registry

            for (receiver_type, method_name), method in delegated_registry._methods.items():
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

        # Initialize agent-specific state
        self._memory = {}
        self._context = {}
        self._conversation_memory = None  # Lazy initialization
        self._llm_resource: LegacyLLMResource = None  # Lazy initialization
        self._llm_resource_instance = None  # Lazy initialization

        # Initialize TUI metrics
        self._metrics = {
            "is_running": False,
            "current_step": "idle",
            "elapsed_time": 0.0,
            "tokens_per_sec": 0.0,
        }

        # Initialize the base StructInstance
        from dana.registry import AGENT_REGISTRY

        super().__init__(struct_type, values, AGENT_REGISTRY)

    def get_metrics(self) -> dict[str, Any]:
        """Get current agent metrics for TUI display.

        Returns:
            Dictionary containing:
            - is_running: bool - Whether agent is currently processing
            - current_step: str - Current processing step
            - elapsed_time: float - Time elapsed for current operation
            - tokens_per_sec: float - Token processing rate
        """
        return self._metrics.copy()

    def update_metric(self, key: str, value: Any) -> None:
        """Update a specific metric value.

        Args:
            key: The metric key to update
            value: The new value for the metric
        """
        if key in self._metrics:
            self._metrics[key] = value

    @property
    def name(self) -> str:
        """Get the agent's name for TUI compatibility."""
        # Return the instance name field value, not the struct type name
        return self._values.get("name", "unnamed_agent")

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

        method = lookup_dana_method(self.__struct_type__.name, "plan")
        if method:
            # User-defined Dana plan() method
            return method(self, sandbox_context, task, context)
        else:
            # Fallback to built-in plan implementation
            return default_plan_method(self, sandbox_context, task, context)

    def solve(self, sandbox_context: SandboxContext, problem: str, context: dict | None = None,
              resources: list[ResourceInstance] | None = None, workflows: list[WorkflowInstance] | None = None) -> Any:
        """Execute agent problem-solving method."""

        method = lookup_dana_method(self.__struct_type__.name, "solve")
        if method:
            # User-defined Dana solve() method
            return method(self,
                          sandbox_context=sandbox_context,
                          problem=problem,
                          context=context,
                          resources=resources,
                          workflows=workflows)
        else:
            # Fallback to built-in solve implementation
            return default_solve_method(self,
                                        sandbox_context=sandbox_context,
                                        problem=problem,
                                        context=context,
                                        resources=resources,
                                        workflows=workflows)

    def remember(self, sandbox_context: SandboxContext, key: str, value: Any) -> Any:
        """Execute agent memory storage method."""

        method = lookup_dana_method(self.__struct_type__.name, "remember")
        if method:
            # User-defined Dana remember() method
            return method(self, sandbox_context, key, value)
        else:
            # Fallback to built-in remember implementation
            return default_remember_method(self, sandbox_context, key, value)

    def recall(self, sandbox_context: SandboxContext, key: str) -> Any:
        """Execute agent memory retrieval method."""

        method = lookup_dana_method(self.__struct_type__.name, "recall")
        if method:
            # User-defined Dana recall() method
            return method(self, sandbox_context, key)
        else:
            # Fallback to built-in recall implementation
            return default_recall_method(self, sandbox_context, key)

    def reason(self, sandbox_context: SandboxContext, premise: str, context: dict | None = None,
               resources: list[ResourceInstance] | None = None) -> Any:
        """Execute agent reasoning method."""

        method = lookup_dana_method(self.__struct_type__.name, "reason")
        if method:
            # User-defined Dana reason() method
            return method(self,
                          sandbox_context=sandbox_context,
                          premise=premise,
                          context=context,
                          resources=resources)
        else:
            # Fallback to built-in reason implementation
            return default_reason_method(self,
                                         sandbox_context=sandbox_context,
                                         premise=premise,
                                         context=context,
                                         resources=resources)

    def chat(self, sandbox_context: SandboxContext, message: str, context: dict | None = None, max_context_turns: int = 5) -> Any:
        """Execute agent chat method."""

        method = lookup_dana_method(self.__struct_type__.name, "chat")
        if method:
            # User-defined Dana chat() method
            return method(self, sandbox_context, message, context, max_context_turns)
        else:
            return default_chat_method(self, sandbox_context, message, context, max_context_turns)

    def old_chat(self, sandbox_context: SandboxContext, message: str, context: dict | None = None, max_context_turns: int = 5) -> Any:
        """Execute agent chat method."""
        from dana.core.concurrency.promise_factory import PromiseFactory

        method = lookup_dana_method(self.__struct_type__.name, "chat")
        if method:
            return method(self, sandbox_context, message, context, max_context_turns)

        # Initialize conversation memory before creating the Promise
        self._initialize_conversation_memory()

        # Wrap the _chat_impl call in an EagerPromise for asynchronous execution
        def chat_computation():
            return self._chat_impl(sandbox_context, message, context, max_context_turns)

        def save_conversation_callback(response):
            """Callback to save the conversation turn when the response is ready."""
            if self._conversation_memory:
                self._conversation_memory.add_turn(message, response)

        return PromiseFactory.create_promise(computation=chat_computation, on_delivery=save_conversation_callback)

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
            from dana.core.builtin_types.resource.builtins.llm_resource_type import LLMResourceType

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

            if self._llm_resource_instance and self._llm_resource_instance.is_available:
                return self._llm_resource_instance

            # Fallback to sandbox context if agent's LLM is not available
            if sandbox_context is not None:
                # Use the system LLM resource from context
                system_llm = sandbox_context.get_system_llm_resource()
                if system_llm is not None:
                    return system_llm

                # Fallback to looking for any LLM resource in context
                try:
                    resources = sandbox_context.get_resources()
                    for _, resource in resources.items():
                        if hasattr(resource, "kind") and resource.kind == "llm":
                            return resource
                except Exception:
                    pass
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

    def _chat_impl(
        self, sandbox_context: SandboxContext | None = None, message: str = "", context: dict | None = None, max_context_turns: int = 5
    ) -> str:
        """Implementation of chat functionality. Returns the response string directly."""
        # Build conversation context - initialize if not already done
        if self._conversation_memory is None:
            self._initialize_conversation_memory()

        # Ensure conversation memory is available
        if self._conversation_memory is None:
            # Fallback if initialization failed
            conversation_context = ""
        else:
            conversation_context = self._conversation_memory.build_llm_context(message, include_summaries=True, max_turns=max_context_turns)

        # Try to get LLM resource - prioritize agent's own LLM resource
        llm_resource = self._get_llm_resource(sandbox_context)

        if llm_resource:
            try:
                # Build system prompt with agent description
                system_prompt = self._build_agent_description()

                # Add conversation context if available
                if conversation_context.strip():
                    system_prompt += f"\n\nPrevious conversation:\n{conversation_context}"

                # Prepare messages
                messages = [{"role": "user", "content": message}]

                # Use the simplified chat completion method
                result = llm_resource.chat_completion(messages=messages, system_prompt=system_prompt, context=context)

            except Exception as e:
                result = f"I encountered an error while processing your message: {str(e)}"
        else:
            # For fallback response, execute synchronously
            result = self._generate_fallback_response(message, conversation_context)

        return result

    def _plan_impl(self, sandbox_context: SandboxContext, task: str, context: dict | None = None) -> str:
        """Implementation of planning functionality using py_reason with POET enhancements."""
        try:
            from dana.libs.corelib.py_wrappers.py_reason import py_reason

            # Build agent description for context
            agent_description = self._build_agent_description()

            # Create planning prompt
            planning_prompt = f"""
You are {agent_description}

Please create a detailed plan for accomplishing this task: {task}

Consider the agent's capabilities and context. Return a structured plan with clear steps.
"""

            # Prepare options for py_reason
            options = {
                "system_message": agent_description,
                "temperature": 0.7,
            }

            # Add any additional context
            if context:
                options["context"] = context

            # Use py_reason for sophisticated planning with POET enhancements
            result = py_reason(sandbox_context, planning_prompt, options)

            return str(result)

        except Exception as e:
            # Fallback to simple response if py_reason fails
            agent_fields = ", ".join(f"{k}: {v}" for k, v in self.__dict__.items() if not k.startswith("_"))
            return f"Agent {self.agent_type.name} planning: {task} (fields: {agent_fields}) - Error: {str(e)}"

    def _solve_impl(self, sandbox_context: SandboxContext, problem: str, context: dict | None = None,
                    resources: list[ResourceInstance] | None = None, workflows: list[WorkflowInstance] | None = None) -> str:
        """Implementation of problem-solving functionality using py_reason with POET enhancements."""
        try:
            from dana.libs.corelib.py_wrappers.py_reason import py_reason

            # Build agent description for context
            agent_description = self._build_agent_description()

            if workflows:
                # Handle multiple workflows - execute each one and collect results
                workflow_results: list[str] = []

                for workflow in workflows:
                    print(f'Executing workflow: `{workflow}`...')
                    workflow_results.append(f"""
-----------------------------------------
Result from workflow `{workflow}`:
-----------------------------------------
{workflow(resources)}
""")

                workflow_results_str = '\n\n\n'.join(workflow_results)

                solving_prompt = f"""
You are {agent_description}

Given the following problem:

PROBLEM:
```
{problem}
```

And the following result(s) from expert workflow(s):

RESULT(S) FROM EXPERT WORKFLOW(S):
```
{workflow_results_str}
```

Return your best conclusion about / solution to the posed problem.
"""

            else:
                solving_prompt = f"""
You are {agent_description}

Please provide a solution to this problem: {problem}

Use the agent's capabilities and context to formulate an effective response. Return a comprehensive solution.
"""

            # Prepare options for py_reason
            options = {
                "system_message": agent_description,
                "temperature": 0.7,
            }

            # Add any additional context
            if context:
                options["context"] = context

            # Use py_reason for sophisticated problem-solving with POET enhancements
            result = py_reason(sandbox_context, solving_prompt, options)

            return str(result)

        except Exception as e:
            # Fallback to simple response if py_reason fails
            agent_fields = ", ".join(f"{k}: {v}" for k, v in self.__dict__.items() if not k.startswith("_"))
            return f"Agent {self.agent_type.name} solving: {problem} (fields: {agent_fields}) - Error: {str(e)}"

    def _remember_impl(self, sandbox_context: SandboxContext, key: str, value: Any) -> bool:
        """Implementation of memory storage functionality. Returns success status directly."""
        # Initialize memory if it doesn't exist
        try:
            self._memory[key] = value
        except AttributeError:
            # Memory not initialized yet, create it
            self._memory = {key: value}
        return True

    def _recall_impl(self, sandbox_context: SandboxContext, key: str) -> Any:
        """Implementation of memory retrieval functionality. Returns the stored value directly."""
        # Use try/except instead of hasattr to avoid sandbox restrictions
        try:
            return self._memory.get(key, None)
        except AttributeError:
            # Memory not initialized yet
            return None

    def _reason_impl(self, sandbox_context: SandboxContext, premise: str, context: dict | None = None,
                     resources: list[ResourceInstance] | None = None) -> str:
        """Implementation of reasoning functionality using py_reason with POET enhancements."""
        try:
            from dana.libs.corelib.py_wrappers.py_reason import py_reason

            # Build agent description for context
            agent_description = self._build_agent_description()

            # Create reasoning prompt
            reasoning_prompt = f"""
You are {agent_description}

Please reason about the following premise: {premise}

Apply logical thinking, consider implications, and draw reasonable conclusions based on the available information.
Return your reasoning process and conclusions.
"""

            # Prepare options for py_reason
            options = {
                "system_message": agent_description,
                "temperature": 0.7,
            }

            # Add any additional context
            if context:
                options["context"] = context

            # Use py_reason for sophisticated reasoning with POET enhancements
            result = py_reason(sandbox_context, reasoning_prompt, options)

            return result

        except Exception as e:
            # Fallback to simple response if py_reason fails
            agent_fields = ", ".join(f"{k}: {v}" for k, v in self.__dict__.items() if not k.startswith("_"))
            return f"Agent {self.agent_type.name} reasoning about: {premise} (fields: {agent_fields}) - Error: {str(e)}"

    def get_conversation_stats(self) -> dict:
        """Get conversation statistics for this agent."""
        if self._conversation_memory is None:
            return {
                "error": "Conversation memory not initialized",
                "total_messages": 0,
                "total_turns": 0,
                "active_turns": 0,
                "summary_count": 0,
                "session_count": 0,
            }
        return self._conversation_memory.get_statistics()

    def clear_conversation_memory(self) -> bool:
        """Clear the conversation memory for this agent."""
        if self._conversation_memory is None:
            return False
        self._conversation_memory.clear()
        return True


# Re-export for backward compatibility
__all__ = getattr(globals(), "__all__", [])
__all__.extend(
    [
        "AgentTypeRegistry",
        "global_agent_type_registry",
        "register_agent_type",
        "get_agent_type",
        "create_agent_instance",
    ]
)
