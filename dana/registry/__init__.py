"""
Dana Global Registry System

Unified registry system for all Dana components with specialized storage for different types.

This module provides a centralized registry that consolidates all Dana registries:
- TypeRegistry: Agent, Resource, and Struct type definitions
- StructFunctionRegistry: Struct method dispatch with composite keys
- ModuleRegistry: Module loading and dependency tracking
- FunctionRegistry: Function registration and dispatch
- InstanceRegistry: Optional instance tracking and lifecycle management

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .function_registry import FunctionRegistry
from .global_registry import GlobalRegistry
from .instance_registry import InstanceRegistry
from .module_registry import ModuleRegistry
from .struct_function_registry import StructFunctionRegistry
from .type_registry import TypeRegistry

# Global singleton instance
GLOBAL_REGISTRY: GlobalRegistry = GlobalRegistry()
MODULE_REGISTRY: ModuleRegistry = GLOBAL_REGISTRY.modules
TYPE_REGISTRY: TypeRegistry = GLOBAL_REGISTRY.types
FUNCTION_REGISTRY: FunctionRegistry = GLOBAL_REGISTRY.functions
STRUCT_FUNCTION_REGISTRY: StructFunctionRegistry = GLOBAL_REGISTRY.struct_functions


def get_global_registry() -> GlobalRegistry:
    """Get the global registry singleton instance."""
    global GLOBAL_REGISTRY
    return GLOBAL_REGISTRY


# Convenience functions for common operations
def register_agent_type(agent_type) -> None:
    """Register an agent type in the global registry."""
    registry = get_global_registry()
    registry.types.register_agent_type(agent_type)


def register_resource_type(resource_type) -> None:
    """Register a resource type in the global registry."""
    registry = get_global_registry()
    registry.types.register_resource_type(resource_type)


def register_struct_type(struct_type) -> None:
    """Register a struct type in the global registry."""
    registry = get_global_registry()
    registry.types.register_struct_type(struct_type)


def get_agent_type(name: str):
    """Get an agent type from the global registry."""
    registry = get_global_registry()
    return registry.types.get_agent_type(name)


def get_resource_type(name: str):
    """Get a resource type from the global registry."""
    registry = get_global_registry()
    return registry.types.get_resource_type(name)


def get_struct_type(name: str):
    """Get a struct type from the global registry."""
    registry = get_global_registry()
    return registry.types.get_struct_type(name)


def register_struct_function(receiver_type: str, method_name: str, func) -> None:
    """Register a struct function in the global registry."""
    registry = get_global_registry()
    registry.struct_functions.register_method(receiver_type, method_name, func)


def lookup_struct_function(receiver_type: str, method_name: str):
    """Lookup a struct function in the global registry."""
    registry = get_global_registry()
    return registry.struct_functions.lookup_method(receiver_type, method_name)


def has_struct_function(receiver_type: str, method_name: str) -> bool:
    """Check if a struct function exists in the global registry."""
    registry = get_global_registry()
    return registry.struct_functions.has_method(receiver_type, method_name)


def clear_all() -> None:
    """Clear all registries (for testing)."""
    registry = get_global_registry()
    registry.clear_all()


__all__ = [
    "GLOBAL_REGISTRY",
    "GlobalRegistry",
    "TypeRegistry",
    "StructFunctionRegistry",
    "ModuleRegistry",
    "FunctionRegistry",
    "InstanceRegistry",
    "get_global_registry",
    "register_agent_type",
    "register_resource_type",
    "register_struct_type",
    "get_agent_type",
    "get_resource_type",
    "get_struct_type",
    "register_struct_function",
    "lookup_struct_function",
    "has_struct_function",
    "clear_all",
]
