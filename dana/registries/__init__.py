"""
Dana Registries

Centralized registry system for all Dana components.

This module consolidates all core registries into a single, well-organized location:
- FunctionRegistry: Function registration and dispatch
- StructTypeRegistry: Struct type definitions
- ResourceTypeRegistry: Resource type definitions
- AgentTypeRegistry: Agent type definitions
- MethodRegistry: Method registration for structs
- TypeAwareMethodRegistry: Type-aware method dispatch
- ModuleRegistry: Module loading and dependency tracking

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# Import all registries for easy access
# Re-export FunctionType from its original location for now
from dana.core.lang.interpreter.executor.function_resolver import FunctionType

from .function_registry import FunctionMetadata, FunctionRegistry, RegistryAdapter, global_function_registry
from .method_registry import (
    MethodRegistry,
    TypeAwareMethodRegistry,
    global_method_registry,
    global_type_aware_method_registry,
    universal_dana_method_registry,
)
from .module_registry import ModuleRegistry, global_module_registry
from .type_registry import (
    AgentTypeRegistry,
    ResourceTypeRegistry,
    StructTypeRegistry,
    create_agent_instance,
    get_agent_type,
    global_agent_type_registry,
    global_resource_type_registry,
    global_struct_type_registry,
    register_agent_type,
)

__all__ = [
    # Function registration
    "FunctionRegistry",
    "FunctionMetadata",
    "FunctionType",
    "RegistryAdapter",
    "global_function_registry",
    # Type registration
    "StructTypeRegistry",
    "ResourceTypeRegistry",
    "global_struct_type_registry",
    "global_resource_type_registry",
    # Method registration
    "MethodRegistry",
    "TypeAwareMethodRegistry",
    "global_method_registry",
    "global_type_aware_method_registry",
    "universal_dana_method_registry",
    # Agent registration
    "AgentTypeRegistry",
    "global_agent_type_registry",
    "register_agent_type",
    "get_agent_type",
    "create_agent_instance",
    # Module registration
    "ModuleRegistry",
    "global_module_registry",
]
