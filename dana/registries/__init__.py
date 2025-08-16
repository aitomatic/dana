"""
DEPRECATED: Dana Registries

This module has been deprecated and moved to dana.registry.
Please update your imports to use the new unified registry system.

The new registry system provides:
- dana.registry.FunctionRegistry: Function registration and dispatch
- dana.registry.TypeRegistry: Unified type registry for agents, resources, and structs
- dana.registry.StructFunctionRegistry: Struct method dispatch
- dana.registry.ModuleRegistry: Module loading and dependency tracking
- dana.registry.GlobalRegistry: Unified global registry instance

Migration guide:
- Replace 'from dana.registries import *' with 'from dana.registry import *'
- Replace 'from dana.registries.function_registry import FunctionRegistry' with 'from dana.registry.function_registry import FunctionRegistry'
- Replace 'from dana.registries.type_registry import *' with 'from dana.registry.type_registry import *'

This module will be removed in a future version.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import warnings

warnings.warn(
    "dana.registries is deprecated. Please use dana.registry instead. This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Import from the new registry system for backward compatibility
from dana.registry import (
    FunctionRegistry,
    ModuleRegistry,
    StructFunctionRegistry,
    TypeRegistry,
    get_agent_type,
    get_global_registry,
    get_resource_type,
    get_struct_type,
    has_struct_function,
    lookup_struct_function,
    register_agent_type,
    register_resource_type,
    register_struct_function,
    register_struct_type,
)

# Create backward compatibility aliases
AgentTypeRegistry = TypeRegistry
ResourceTypeRegistry = TypeRegistry
StructTypeRegistry = TypeRegistry
MethodRegistry = StructFunctionRegistry


# Create a wrapper class that provides class methods for backward compatibility
class TypeAwareMethodRegistry:
    """Type-aware method registry with class methods for backward compatibility."""

    @classmethod
    def register_method(cls, receiver_type: str, method_name: str, func) -> None:
        """Register a method for a receiver type."""
        register_struct_function(receiver_type, method_name, func)

    @classmethod
    def lookup_method(cls, receiver_type: str, method_name: str):
        """Lookup a method for a receiver type."""
        return lookup_struct_function(receiver_type, method_name)

    @classmethod
    def has_method(cls, receiver_type: str, method_name: str) -> bool:
        """Check if a method exists for a receiver type."""
        return has_struct_function(receiver_type, method_name)

    @classmethod
    def lookup_method_for_instance(cls, instance, method_name: str):
        """Lookup method for a specific instance (extracts type automatically)."""
        return global_registry.struct_functions.lookup_method_for_instance(instance, method_name)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered methods (for testing)."""
        global_registry.struct_functions.clear()

    def __init__(self):
        """Initialize the wrapper instance."""
        # This is needed for backward compatibility when code creates an instance
        pass

    @property
    def _storage(self):
        """Backward compatibility property for accessing the internal storage."""
        return global_registry.struct_functions._methods


# Create backward compatibility instances
global_registry = get_global_registry()
global_function_registry = global_registry.functions
global_agent_type_registry = global_registry.types
global_resource_type_registry = global_registry.types
global_struct_type_registry = global_registry.types
global_method_registry = global_registry.struct_functions
global_type_aware_method_registry = global_registry.struct_functions
universal_dana_method_registry = global_registry.struct_functions
global_module_registry = global_registry.modules


# Backward compatibility function
def create_agent_instance(name, field_values=None, context=None):
    """Create an agent instance (backward compatibility)."""
    from dana.agent import AgentInstance

    agent_type = get_agent_type(name)
    if agent_type is None:
        raise ValueError(f"Agent type '{name}' not found")
    return AgentInstance(agent_type, field_values or {})


__all__ = [
    # Function registration
    "FunctionRegistry",
    "global_function_registry",
    # Type registration
    "StructTypeRegistry",
    "ResourceTypeRegistry",
    "AgentTypeRegistry",
    "global_struct_type_registry",
    "global_resource_type_registry",
    "global_agent_type_registry",
    # Method registration
    "MethodRegistry",
    "TypeAwareMethodRegistry",
    "global_method_registry",
    "global_type_aware_method_registry",
    "universal_dana_method_registry",
    # Agent registration
    "register_agent_type",
    "get_agent_type",
    "create_agent_instance",
    # Resource registration
    "register_resource_type",
    "get_resource_type",
    # Struct registration
    "register_struct_type",
    "get_struct_type",
    "register_struct_function",
    "lookup_struct_function",
    "has_struct_function",
    # Module registration
    "ModuleRegistry",
    "global_module_registry",
]
