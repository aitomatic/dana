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
