"""
Dana Global Registry System

Unified registry system for all Dana components with specialized storage for different types.

This module provides a centralized registry that consolidates all Dana registries:
- TypeRegistry: Agent, Resource, and Struct type definitions
- StructFunctionRegistry: Struct method dispatch with composite keys
- ModuleRegistry: Module loading and dependency tracking
- FunctionRegistry: Function registration and dispatch
- StructRegistry: Optional instance tracking and lifecycle management

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any

from .agent_registry import AgentRegistry
from .function_registry import FunctionRegistry
from .global_registry import GlobalRegistry
from .instance_registry import StructRegistry
from .module_registry import ModuleRegistry
from .resource_registry import ResourceRegistry
from .type_registry import TypeRegistry

# Global singleton instance
GLOBAL_REGISTRY: GlobalRegistry = GlobalRegistry()
MODULE_REGISTRY: ModuleRegistry = GLOBAL_REGISTRY.modules

TYPE_REGISTRY: TypeRegistry = GLOBAL_REGISTRY.types

FUNCTION_REGISTRY: FunctionRegistry = GLOBAL_REGISTRY.functions

# Note: STRUCT_FUNCTION_REGISTRY has been removed. All struct method operations
# should go through FUNCTION_REGISTRY which delegates to the internal StructFunctionRegistry automatically.

AGENT_REGISTRY: AgentRegistry = GLOBAL_REGISTRY.agents
RESOURCE_REGISTRY: ResourceRegistry = GLOBAL_REGISTRY.resources
WORKFLOW_REGISTRY: StructRegistry = GLOBAL_REGISTRY.workflows

# def get_global_registry() -> GlobalRegistry:
#     """Get the global registry singleton instance."""
#     global GLOBAL_REGISTRY
#     return GLOBAL_REGISTRY


# Convenience functions for common operations
def register_agent_type(agent_type) -> None:
    """Register an agent type in the global registry."""
    TYPE_REGISTRY.register_agent_type(agent_type)


def register_resource_type(resource_type) -> None:
    """Register a resource type in the global registry."""
    TYPE_REGISTRY.register_resource_type(resource_type)


def register_struct_type(struct_type) -> None:
    """Register a struct type in the global registry."""
    TYPE_REGISTRY.register_struct_type(struct_type)


def register_interface_type(interface_type) -> None:
    """Register an interface type in the global registry."""
    TYPE_REGISTRY.register_interface_type(interface_type)


def register_workflow_type(workflow_type) -> None:
    """Register a workflow type in the global registry."""
    TYPE_REGISTRY.register_workflow_type(workflow_type)


def get_type(name: str) -> Any:
    """Get any type by name from the global registry."""
    return TYPE_REGISTRY.get_type(name)


def has_type(name: str) -> bool:
    """Check if any type exists in the global registry."""
    return TYPE_REGISTRY.has_type(name)


def get_agent_type(name: str):
    """Get an agent type from the global registry."""
    return TYPE_REGISTRY.get_agent_type(name)


def get_resource_type(name: str):
    """Get a resource type from the global registry."""
    return TYPE_REGISTRY.get_resource_type(name)


def get_struct_type(name: str):
    """Get a struct type from the global registry."""
    return TYPE_REGISTRY.get_struct_type(name)


def get_workflow_type(name: str):
    """Get a workflow type from the global registry."""
    return TYPE_REGISTRY.get_workflow_type(name)


def register_struct_function(receiver_type: str, method_name: str, func) -> None:
    """Register a struct function in the global registry.

    Note: This uses the unified FUNCTION_REGISTRY which delegates to the internal StructFunctionRegistry.
    All struct method operations should go through FUNCTION_REGISTRY for consistency.
    """
    FUNCTION_REGISTRY.register_struct_function(receiver_type, method_name, func)


def lookup_struct_function(receiver_type: str, method_name: str):
    """Lookup a struct function in the global registry.

    Note: This uses the unified FUNCTION_REGISTRY which delegates to the internal StructFunctionRegistry.
    All struct method operations should go through FUNCTION_REGISTRY for consistency.
    """
    return FUNCTION_REGISTRY.lookup_struct_function(receiver_type, method_name)


def has_struct_function(receiver_type: str, method_name: str) -> bool:
    """Check if a struct function exists in the global registry.

    Note: This uses the unified FUNCTION_REGISTRY which delegates to the internal StructFunctionRegistry.
    All struct method operations should go through FUNCTION_REGISTRY for consistency.
    """
    return FUNCTION_REGISTRY.has_struct_function(receiver_type, method_name)


def clear_all() -> None:
    """Clear all registries (for testing)."""
    GLOBAL_REGISTRY.clear_all()


__all__ = [
    "AGENT_REGISTRY",
    "FUNCTION_REGISTRY",
    "AgentRegistry",
    "GLOBAL_REGISTRY",
    "GlobalRegistry",
    "TYPE_REGISTRY",
    "TypeRegistry",
    "MODULE_REGISTRY",
    "ModuleRegistry",
    "StructRegistry",
    "WORKFLOW_REGISTRY",
    "ResourceRegistry",
    "clear_all",
]
