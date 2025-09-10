"""
Agent Type System

This module defines the AgentType class which extends StructType to provide
agent-specific functionality and capabilities.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from dana.core.builtins.struct_system import StructType

from .utils import has_dana_method, lookup_dana_method, register_dana_method


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
        from .agent_instance import AgentInstance

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
