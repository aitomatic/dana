"""
Agent Struct System for Dana Language (Unified with Struct System)

This module implements agent capabilities by extending the struct system.
AgentStructType inherits from StructType, and AgentStructInstance inherits from StructInstance.

Design Reference: dana/agent/.design/3d_methodology_base_agent_unification.md
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dana.builtin_types.workflow_system import WorkflowType

from dana.builtin_types.struct_system import StructInstance, StructType
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
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
    from dana.builtin_types.agent_system import AgentInstance

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
    agent_instance: "AgentInstance", sandbox_context: SandboxContext, problem: str, user_context: dict | None = None
) -> Any:
    """Default solve method for agent structs - delegates to instance method."""

    # Simply delegate to the built-in implementation
    # The main solve() method will handle Promise wrapping
    def wrapper():
        return agent_instance._solve_impl(sandbox_context, problem, user_context)

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
    agent_instance: "AgentInstance", sandbox_context: SandboxContext, premise: str, context: dict | None = None
) -> Any:
    """Default reason method for agent structs - delegates to instance method."""

    # Simply delegate to the built-in implementation
    # The main reason() method will handle Promise wrapping
    def wrapper():
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

    def plan(self, task: str, context: dict | None = None, sandbox_context: SandboxContext | None = None) -> Any:
        """Execute agent planning method."""

        # If no sandbox_context provided, try to get it from current Dana context
        if sandbox_context is None:
            sandbox_context = self._get_current_dana_context()

        # If still no sandbox_context, create a minimal one or handle gracefully
        if sandbox_context is None:
            # For now, create a minimal sandbox context for Python usage
            from dana.core.lang.sandbox_context import SandboxContext

            sandbox_context = SandboxContext()

        method = lookup_dana_method(self.__struct_type__.name, "plan")
        if method:
            # User-defined Dana plan() method
            return method(self, sandbox_context, task, context)
        else:
            # Default implementation: create and return a workflow instance
            from dana.builtin_types.workflow_system import WorkflowInstance

            workflow_type = self._create_workflow_type(task)
            return WorkflowInstance(workflow_type, {})

    def solve(self, problem: str, context: dict | None = None, sandbox_context: SandboxContext | None = None) -> Any:
        """Execute agent problem-solving method."""

        # If no sandbox_context provided, try to get it from current Dana context
        if sandbox_context is None:
            sandbox_context = self._get_current_dana_context()

        # If still no sandbox_context, create a minimal one or handle gracefully
        if sandbox_context is None:
            # For now, create a minimal sandbox context for Python usage
            from dana.core.lang.sandbox_context import SandboxContext

            sandbox_context = SandboxContext()

        method = lookup_dana_method(self.__struct_type__.name, "solve")
        if method:
            # User-defined Dana solve() method
            return method(self, sandbox_context, problem, context)
        else:
            # Fallback to built-in solve implementation
            return default_solve_method(self, sandbox_context, problem, context)

    def remember(self, key: str, value: Any, sandbox_context: SandboxContext | None = None) -> Any:
        """Execute agent memory storage method."""

        # If no sandbox_context provided, try to get it from current Dana context
        if sandbox_context is None:
            sandbox_context = self._get_current_dana_context()

        # If still no sandbox_context, create a minimal one or handle gracefully
        if sandbox_context is None:
            # For now, create a minimal sandbox context for Python usage
            from dana.core.lang.sandbox_context import SandboxContext

            sandbox_context = SandboxContext()

        method = lookup_dana_method(self.__struct_type__.name, "remember")
        if method:
            # User-defined Dana remember() method
            return method(self, sandbox_context, key, value)
        else:
            # Fallback to built-in remember implementation
            return default_remember_method(self, sandbox_context, key, value)

    def recall(self, key: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Execute agent memory retrieval method."""

        # If no sandbox_context provided, try to get it from current Dana context
        if sandbox_context is None:
            sandbox_context = self._get_current_dana_context()

        # If still no sandbox_context, create a minimal one or handle gracefully
        if sandbox_context is None:
            # For now, create a minimal sandbox context for Python usage
            from dana.core.lang.sandbox_context import SandboxContext

            sandbox_context = SandboxContext()

        method = lookup_dana_method(self.__struct_type__.name, "recall")
        if method:
            # User-defined Dana recall() method
            return method(self, sandbox_context, key)
        else:
            # Fallback to built-in recall implementation
            return default_recall_method(self, sandbox_context, key)

    def reason(self, premise: str, context: dict | None = None, sandbox_context: SandboxContext | None = None) -> Any:
        """Execute agent reasoning method."""

        # If no sandbox_context provided, try to get it from current Dana context
        if sandbox_context is None:
            sandbox_context = self._get_current_dana_context()

        # If still no sandbox_context, create a minimal one or handle gracefully
        if sandbox_context is None:
            # For now, create a minimal sandbox context for Python usage
            from dana.core.lang.sandbox_context import SandboxContext

            sandbox_context = SandboxContext()

        method = lookup_dana_method(self.__struct_type__.name, "reason")
        if method:
            # User-defined Dana reason() method
            return method(self, sandbox_context, premise, context)
        else:
            # Fallback to built-in reason implementation
            return default_reason_method(self, sandbox_context, premise, context)

    def chat(
        self, message: str, context: dict | None = None, max_context_turns: int = 5, sandbox_context: SandboxContext | None = None
    ) -> Any:
        """Execute agent chat method."""

        # If no sandbox_context provided, try to get it from current Dana context
        if sandbox_context is None:
            sandbox_context = self._get_current_dana_context()

        # If still no sandbox_context, create a minimal one or handle gracefully
        if sandbox_context is None:
            # For now, create a minimal sandbox context for Python usage
            from dana.core.lang.sandbox_context import SandboxContext

            sandbox_context = SandboxContext()

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
            from dana.builtin_types.resource.builtins.llm_resource_type import LLMResourceType
            from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource

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
        """Implementation of chat functionality that returns a string response."""
        try:
            # Try to use LLM if available
            llm_resource = self._get_llm_resource(sandbox_context)
            if llm_resource is not None:
                # Build system prompt
                system_prompt = self._build_agent_description()

                # Get conversation context if available
                conversation_context = []
                if self._conversation_memory:
                    recent_turns = self._conversation_memory.get_recent_context(max_context_turns)
                    for turn in recent_turns:
                        conversation_context.append({"role": "user", "content": turn["user_input"]})
                        conversation_context.append({"role": "assistant", "content": turn["agent_response"]})

                # Add current message
                conversation_context.append({"role": "user", "content": message})

                # Call LLM
                response = llm_resource.chat_completion(conversation_context, system_prompt=system_prompt, context=context)
                return response
            else:
                # Fallback to simple responses when no LLM is available
                return self._generate_fallback_response(message, str(context) if context else "")
        except Exception as e:
            # Fallback to error response
            return f"I encountered an error while processing your message: {str(e)}"

    def _plan_impl(self, sandbox_context: SandboxContext, task: str, context: dict | None = None) -> str:
        """Implementation of planning functionality that returns string results for compatibility."""
        # Handle None or empty task
        if task is None:
            task = "None"
        elif not isinstance(task, str):
            task = str(task)

        print(f"📋 [{self.__struct_type__.name}] PLAN: Planning task: '{task}'")
        print(f"   Context: {context}")

        from dana.builtin_types.workflow_system import WorkflowInstance

        # Create appropriate workflow type based on task
        workflow_type = self._create_workflow_type(task)
        print(f"   📋 Created workflow type: {workflow_type.name}")

        # Create WorkflowInstance for internal use
        workflow_instance = WorkflowInstance(
            struct_type=workflow_type, values={"name": workflow_type.name, "fsm": f"workflow_for_{task.replace(' ', '_').lower()}"}
        )
        print(f"   ✅ Created WorkflowInstance: {workflow_instance}")

        # Return string result for test compatibility
        return f"Planning task '{task}' using {self.__struct_type__.name} with workflow {workflow_type.name}"

    def _solve_impl(self, sandbox_context: SandboxContext, problem: str, context: dict | None = None) -> str:
        """Implementation of problem-solving functionality that returns string results for compatibility.

        Implements the 4 use cases from the Agent-Workflow FSM specification:
        - Use Case 0: Simple computation (e.g., "47 + 89")
        - Use Case 1: Equipment health checks
        - Use Case 2: Data analysis
        - Use Case 3: Complex reasoning
        """
        # Handle None or empty problem
        if problem is None:
            problem = "None"
        elif not isinstance(problem, str):
            problem = str(problem)

        print(f"🔍 [{self.__struct_type__.name}] SOLVE: Analyzing problem: '{problem}'")
        print(f"   Context: {context}")

        # FSM State Tracking
        print("   🎯 FSM STATE: ANALYZING → Parsing problem type")

        problem_lower = problem.lower()

        # Use LLM to analyze and classify the problem using the decision tree
        print(f"   🤖 Using LLM to analyze problem: '{problem}'")

        # Get LLM analysis of the problem using the decision tree
        llm_analysis = self._analyze_problem_with_llm(problem, sandbox_context)
        print(f"   📊 LLM Analysis: {llm_analysis}")

        # Determine approach based on LLM decision tree analysis
        decision = llm_analysis.get("decision", "unknown")
        confidence = llm_analysis.get("confidence", 0.0)
        action = llm_analysis.get("action", {})

        print(f"   🎯 LLM decision: {decision} (confidence: {confidence})")
        print(f"   🎯 Action type: {action.get('type', 'unknown')}")

        # Route based on LLM decision tree and convert to string for compatibility
        if decision == "direct_llm":
            result = self._handle_direct_llm_solution(problem, action, llm_analysis)
            return f"Solving problem '{problem}' using {self.__struct_type__.name} with direct LLM solution: {result.get('result', 'No result')}"
        elif decision == "dana_code":
            result = self._handle_dana_code_generation(problem, action, llm_analysis, sandbox_context)
            return f"Solving problem '{problem}' using {self.__struct_type__.name} with Dana code generation: {result.get('result', 'No result')}"
        elif decision == "existing_workflow":
            result = self._handle_existing_workflow(problem, action, llm_analysis)
            return (
                f"Solving problem '{problem}' using {self.__struct_type__.name} with existing workflow: {result.get('status', 'No status')}"
            )
        elif decision == "custom_workflow":
            result = self._handle_custom_workflow_generation(problem, action, llm_analysis)
            return (
                f"Solving problem '{problem}' using {self.__struct_type__.name} with custom workflow: {result.get('status', 'No status')}"
            )
        else:
            result = self._handle_general_reasoning(problem, llm_analysis)
            return f"Solving problem '{problem}' using {self.__struct_type__.name} with general reasoning: {result.get('response', 'No response')}"

        # Use Case 1: Equipment health and status checks (Generate Workflow)
        if any(keyword in problem_lower for keyword in ["equipment", "line", "status", "health", "check"]):
            print(f"   🔧 Detected equipment/health check in: '{problem}'")
            print("   🎯 FSM STATE: ANALYZING → WORKFLOW_GENERATION")

            # Generate workflow for equipment health check
            from dana.builtin_types.workflow_system import WorkflowInstance

            workflow_type = self._create_workflow_type(problem)
            workflow_instance = WorkflowInstance(
                struct_type=workflow_type, values={"name": workflow_type.name, "fsm": "equipment_health_check_workflow"}
            )

            print(f"   📋 Generated workflow: {workflow_type.name}")
            print("   🎯 FSM STATE: WORKFLOW_GENERATION → WORKFLOW_EXECUTION")

            # Execute the workflow
            workflow_instance.execute(
                {"problem": problem, "equipment_id": "Line3" if "line 3" in problem_lower else "Equipment1", "check_type": "health_status"}
            )

            print("   🎯 FSM STATE: WORKFLOW_EXECUTION → COMPLETED")
            return f"Solving problem '{problem}' using {self.__struct_type__.name} with equipment health workflow: {workflow_type.name}"

        # Use Case 2: Data analysis and sensor data (Generate Workflow)
        if any(keyword in problem_lower for keyword in ["analyze", "data", "sensor", "trend", "anomaly"]):
            print(f"   📊 Detected data analysis in: '{problem}'")
            print("   🎯 FSM STATE: ANALYZING → WORKFLOW_GENERATION")

            # Generate workflow for data analysis
            workflow_type = self._create_workflow_type(problem)
            workflow_instance = WorkflowInstance(
                struct_type=workflow_type, values={"name": workflow_type.name, "fsm": "data_analysis_workflow"}
            )

            print(f"   📋 Generated workflow: {workflow_type.name}")
            print("   🎯 FSM STATE: WORKFLOW_GENERATION → WORKFLOW_EXECUTION")

            # Execute the workflow
            workflow_instance.execute(
                {"problem": problem, "data_source": "sensor_data", "time_range": "past_24_hours", "analysis_type": "trend_analysis"}
            )

            print("   🎯 FSM STATE: WORKFLOW_EXECUTION → COMPLETED")
            return f"Solving problem '{problem}' using {self.__struct_type__.name} with data analysis workflow: {workflow_type.name}"

        # Use Case 3: General reasoning and problem solving
        print("   🤔 No specific pattern detected, using general reasoning")
        print("   🎯 FSM STATE: ANALYZING → GENERAL_REASONING")
        result = {
            "status": "analyzed",
            "problem_type": "general_inquiry",
            "response": f"Analyzed problem: {problem}",
            "reasoning": f"Applied {self.__struct_type__.name} capabilities to understand the request",
            "confidence": 0.75,
            "next_steps": ["gather_more_context", "apply_domain_knowledge"],
            "agent": self.__struct_type__.name,
        }
        print("   🎯 FSM STATE: GENERAL_REASONING → COMPLETED")
        return f"Solving problem '{problem}' using {self.__struct_type__.name} with general reasoning: {result['response']}"

    def _analyze_problem_with_llm(self, problem: str, sandbox_context: SandboxContext) -> dict:
        """Use agent.reason() to analyze and classify the problem using the refined decision tree."""
        try:
            # Create a structured YAML prompt for the refined decision tree
            analysis_prompt = f"""
```yaml
task: "problem_classification"
role: "AI problem solver using decision tree analysis"
problem: "{problem}"

decision_tree:
  - name: "Direct LLM Solution"
    condition: "Problem is within LLM powers to solve directly now"
    action: "Return the answer directly"
    example: "What is 5 + 3? → direct_llm with answer '8'"
  
  - name: "Dana Code Generation"
    condition: "Problem is simple but requires Dana code execution"
    action: "Generate Dana code to be executed"
    example: "Calculate factorial of 5 → dana_code with Dana code to compute factorial"
  
  - name: "Existing Workflow"
    condition: "Problem matches one of the known workflows"
    action: "Use existing workflow"
    example: "Check equipment health → existing_workflow with 'HealthCheckWorkflow'"
  
  - name: "Custom Workflow Generation"
    condition: "Problem is complex and no existing workflow matches"
    action: "Generate custom workflow to be executed"
    example: "Analyze sensor data with custom algorithm → custom_workflow with workflow definition"

output_format:
  structure:
    decision: "direct_llm|dana_code|existing_workflow|custom_workflow"
    confidence: "0.0-1.0"
    reasoning: "detailed explanation of why this approach was chosen"
    action:
      type: "direct_answer|dana_code|workflow_name|workflow_definition"
      content: "the actual answer, Dana code, workflow name, or workflow definition"
    complexity: "simple|moderate|complex"

                   instructions: "Analyze the problem using the decision tree above and return ONLY valid YAML matching the output format structure. No other text."
```
"""

            print("   🤖 Using agent.reason() for decision tree analysis...")

            # Use agent.reason() instead of direct LLM call
            try:
                llm_response = self.reason(analysis_prompt, context={"analysis_type": "decision_tree"}, sandbox_context=sandbox_context)
                print("   ✅ Agent.reason() call successful")
            except Exception as reason_error:
                print(f"   ❌ Agent.reason() call failed: {reason_error}")
                print(f"   🔍 Reason error type: {type(reason_error)}")
                print(f"   🔍 Reason error details: {str(reason_error)}")
                raise reason_error

            print(f"   📊 Raw LLM response: {llm_response}")
            print(f"   📊 Response type: {type(llm_response)}")
            print(f"   📊 Response length: {len(str(llm_response)) if isinstance(llm_response, str) else 'N/A'}")

            # Parse the YAML response
            import yaml

            try:
                print("   🔍 Starting YAML parsing...")

                # Extract the content from the LLM response
                if isinstance(llm_response, str):
                    content = llm_response
                    print(f"   📝 Response is string, length: {len(content)}")
                else:
                    content = str(llm_response)
                    print(f"   📝 Response converted to string, length: {len(content)}")

                # Extract YAML from the content
                start_idx = content.find("decision:")
                if start_idx == -1:
                    start_idx = content.find("Decision:")
                if start_idx == -1:
                    start_idx = 0

                end_idx = content.rfind("\n")
                if end_idx == -1:
                    end_idx = len(content)

                print(f"   🔍 YAML bounds: start={start_idx}, end={end_idx}")

                yaml_str = content[start_idx:end_idx]
                print(f"   📝 Extracted YAML string length: {len(yaml_str)}")
                print(f"   📝 YAML string preview: {yaml_str[:200]}...")

                # Parse YAML
                analysis = yaml.safe_load(yaml_str)
                print("   ✅ YAML parsing successful")

                # Validate required fields
                required_fields = ["decision", "confidence", "reasoning", "action", "complexity"]
                print(f"   🔍 Validating required fields: {required_fields}")
                for field in required_fields:
                    if field not in analysis:
                        print(f"   ❌ Missing required field: {field}")
                        print(f"   📄 Available fields: {list(analysis.keys())}")
                        raise ValueError(f"Missing required field: {field}")
                    else:
                        print(f"   ✅ Field '{field}' present: {type(analysis[field])}")

                print(f"   ✅ LLM decision tree analysis successful: {analysis}")
                return analysis

            except (yaml.YAMLError, ValueError, KeyError) as e:
                print(f"   ❌ Failed to parse LLM response: {e}")
                print(f"   🔍 Error type: {type(e)}")
                print(f"   📄 Raw response: {llm_response}")
                print(f"   📄 Raw response type: {type(llm_response)}")
                return self._fallback_heuristic_analysis(problem)

        except Exception as e:
            print(f"   ❌ LLM analysis failed: {e}")
            return self._fallback_heuristic_analysis(problem)

    def _fallback_heuristic_analysis(self, problem: str) -> dict:
        """Fallback heuristic analysis when LLM is not available."""
        problem_lower = problem.lower()

        # Simple heuristic analysis
        if any(op in problem for op in ["+", "-", "*", "/", "="]):
            return {
                "problem_type": "arithmetic",
                "confidence": 0.9,
                "recommended_approach": "direct_solve",
                "reasoning": "Contains mathematical operators",
                "complexity": "simple",
            }
        elif any(word in problem_lower for word in ["equipment", "health", "check", "status"]):
            return {
                "problem_type": "equipment_health",
                "confidence": 0.85,
                "recommended_approach": "workflow",
                "reasoning": "Equipment health check requires systematic process",
                "complexity": "moderate",
            }
        elif any(word in problem_lower for word in ["analyze", "data", "sensor", "trend"]):
            return {
                "problem_type": "data_analysis",
                "confidence": 0.8,
                "recommended_approach": "workflow",
                "reasoning": "Data analysis requires structured workflow",
                "complexity": "complex",
            }
        else:
            return {
                "problem_type": "general_reasoning",
                "confidence": 0.6,
                "recommended_approach": "general_reasoning",
                "reasoning": "No clear pattern detected, requires reasoning",
                "complexity": "moderate",
            }

    def _handle_direct_llm_solution(self, problem: str, action: dict, llm_analysis: dict) -> dict:
        """Handle problem with direct LLM solution."""
        answer = action.get("content", "No answer provided")

        return {
            "status": "completed",
            "result": answer,
            "problem": problem,
            "llm_analysis": llm_analysis,
            "type": "direct_llm_solution",
            "method": "LLM provided direct answer",
        }

    def _handle_dana_code_generation(self, problem: str, action: dict, llm_analysis: dict, sandbox_context: SandboxContext) -> dict:
        """Handle problem by generating and executing Dana code."""
        dana_code = action.get("content", "")

        if not dana_code:
            return {"status": "error", "error": "No Dana code provided by LLM", "llm_analysis": llm_analysis, "type": "dana_code_error"}

        try:
            # For now, return the code that would be executed
            # In a full implementation, this would execute the Dana code in the sandbox
            return {
                "status": "completed",
                "result": f"Generated Dana code: {dana_code}",
                "problem": problem,
                "dana_code": dana_code,
                "llm_analysis": llm_analysis,
                "type": "dana_code_generation",
                "method": "LLM generated Dana code for execution",
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to execute Dana code: {e}",
                "llm_analysis": llm_analysis,
                "type": "dana_code_execution_error",
            }

    def _handle_existing_workflow(self, problem: str, action: dict, llm_analysis: dict) -> dict:
        """Handle problem using existing workflow."""
        workflow_name = action.get("content", "")

        if not workflow_name:
            return {
                "status": "error",
                "error": "No workflow name provided by LLM",
                "llm_analysis": llm_analysis,
                "type": "existing_workflow_error",
            }

        try:
            # Create and execute the existing workflow
            from dana.builtin_types.workflow_system import WorkflowInstance

            workflow_type = self._create_workflow_type(problem)
            workflow_instance = WorkflowInstance(
                struct_type=workflow_type, values={"name": workflow_name, "fsm": f"{workflow_name.lower()}_workflow"}
            )

            # Execute the workflow
            workflow_result = workflow_instance.execute({"problem": problem, "llm_analysis": llm_analysis, "workflow_name": workflow_name})

            return workflow_result

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to execute existing workflow: {e}",
                "llm_analysis": llm_analysis,
                "type": "existing_workflow_execution_error",
            }

    def _handle_custom_workflow_generation(self, problem: str, action: dict, llm_analysis: dict) -> dict:
        """Handle problem by generating custom workflow."""
        workflow_definition = action.get("content", "")

        if not workflow_definition:
            return {
                "status": "error",
                "error": "No workflow definition provided by LLM",
                "llm_analysis": llm_analysis,
                "type": "custom_workflow_error",
            }

        try:
            # Create and execute the custom workflow
            from dana.builtin_types.workflow_system import WorkflowInstance

            workflow_type = self._create_workflow_type(problem)
            workflow_instance = WorkflowInstance(struct_type=workflow_type, values={"name": "CustomWorkflow", "fsm": "custom_workflow"})

            # Execute the custom workflow
            workflow_result = workflow_instance.execute(
                {"problem": problem, "llm_analysis": llm_analysis, "workflow_definition": workflow_definition}
            )

            return workflow_result

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to execute custom workflow: {e}",
                "llm_analysis": llm_analysis,
                "type": "custom_workflow_execution_error",
            }

    def _handle_general_reasoning(self, problem: str, llm_analysis: dict) -> dict:
        """Handle problem with general reasoning."""
        return {
            "status": "analyzed",
            "problem_type": "general_reasoning",
            "response": f"Analyzed problem: {problem}",
            "reasoning": f"Applied {self.__struct_type__.name} capabilities with LLM guidance",
            "confidence": llm_analysis.get("confidence", 0.6),
            "llm_analysis": llm_analysis,
            "next_steps": ["gather_more_context", "apply_domain_knowledge"],
            "agent": self.__struct_type__.name,
        }

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

    def _reason_impl(self, sandbox_context: SandboxContext, premise: str, context: dict | None = None) -> dict:
        """Implementation of reasoning functionality using py_reason() for LLM-powered analysis."""
        print(f"🧠 [{self.__struct_type__.name}] REASON: Analyzing premise: '{premise}'")
        print(f"   Context: {context}")

        try:
            # Use py_reason() for LLM-powered reasoning
            from dana.libs.corelib.py_wrappers.py_reason import py_reason

            # Set up context for type-aware reasoning
            if context is None:
                context = {}

            # Add agent context to help with reasoning
            _ = {
                "agent_name": self.__struct_type__.name,
                "agent_type": "AI Agent",
                "reasoning_task": "premise_analysis",
                **context,
            }

            print("   🤖 Calling py_reason() for LLM-powered analysis...")
            print(f"   📝 Premise length: {len(premise)}")
            print(f"   📝 Sandbox context: {type(sandbox_context)}")

            # Call py_reason() with the premise as-is
            try:
                llm_response = py_reason(
                    sandbox_context,
                    premise,
                    options={
                        "temperature": 0.3,  # Lower temperature for more focused reasoning
                        "max_tokens": 800,
                        "format": "text",
                    },
                )
                print("   ✅ py_reason() call successful")
                print(f"   📊 Response type: {type(llm_response)}")
            except Exception as py_reason_error:
                print(f"   ❌ py_reason() call failed: {py_reason_error}")
                print(f"   🔍 py_reason error type: {type(py_reason_error)}")
                print(f"   🔍 py_reason error details: {str(py_reason_error)}")
                raise py_reason_error

            print(f"   📊 LLM reasoning response: {llm_response}")
            return llm_response

        except Exception as e:
            print(f"   ❌ LLM reasoning failed: {e}")
            # Fallback to basic reasoning
            return {
                "analysis": f"Fallback analysis of: {premise}",
                "reasoning_chain": [
                    f"LLM reasoning failed: {e}",
                    f"Applied {self.__struct_type__.name} fallback reasoning",
                    "Used basic logical analysis",
                ],
                "confidence": 0.6,
                "conclusion": f"Reasoning completed with fallback for: {premise}",
                "methodology": "fallback_reasoning",
                "agent": self.__struct_type__.name,
                "error": str(e),
            }

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

    def _get_current_dana_context(self) -> SandboxContext | None:
        """Get the current Dana sandbox context if available."""
        try:
            # Try to get context from Dana runtime environment
            # This would need to be implemented based on how Dana provides context
            # For now, return None to indicate we're not in a Dana environment
            return None
        except Exception:
            return None

    def _create_workflow_type(self, problem: str) -> "WorkflowType":
        """Create a workflow type based on the problem description."""
        print(f"   🔧 [{self.__struct_type__.name}] Creating workflow type for: '{problem}'")

        from dana.builtin_types.workflow_system import WorkflowType

        problem_lower = problem.lower()

        # Determine workflow type based on problem keywords
        # Check more specific keywords first
        if any(keyword in problem_lower for keyword in ["analyze", "data", "sensor"]):
            print("   📊 Detected data analysis keywords")
            name = "DataAnalysisWorkflow"
            docstring = "Workflow for analyzing sensor data"
        elif any(keyword in problem_lower for keyword in ["health", "check", "maintenance"]):
            print("   🔧 Detected health/maintenance keywords")
            name = "HealthCheckWorkflow"
            docstring = "Workflow for checking equipment health"
        elif any(keyword in problem_lower for keyword in ["pipeline", "process"]):
            print("   🔄 Detected pipeline/process keywords")
            name = "PipelineWorkflow"
            docstring = "Workflow for data processing pipeline"
        elif any(keyword in problem_lower for keyword in ["status", "equipment", "line"]):
            print("   📊 Detected status/equipment keywords")
            name = "EquipmentStatusWorkflow"
            docstring = "Workflow for checking equipment status"
        else:
            print("   🤔 No specific keywords detected, using generic workflow")
            name = "GenericWorkflow"
            docstring = "Generic workflow for problem solving"

        # Create workflow type with standard workflow fields
        fields = {
            "name": "str",
            "fsm": "str",  # Placeholder for FSM definition
        }
        field_order = ["name", "fsm"]

        return WorkflowType(name=name, fields=fields, field_order=field_order, docstring=docstring)


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
