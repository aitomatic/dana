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
