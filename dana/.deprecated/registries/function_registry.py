"""
DEPRECATED: Function Registry for Dana

This module has been deprecated and moved to dana.registry.function_registry.
Please update your imports to use the new unified registry system.

Migration guide:
- Replace 'from dana.registries.function_registry import FunctionRegistry' with 'from dana.registry.function_registry import FunctionRegistry'
- Replace 'from dana.registries.function_registry import global_function_registry' with 'from dana.registry import get_global_registry; global_function_registry = get_global_registry().functions'

This module will be removed in a future version.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import warnings

warnings.warn(
    "dana.registries.function_registry is deprecated. Please use dana.registry.function_registry instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

from typing import TYPE_CHECKING

from dana.core.lang.interpreter.executor.function_resolver import FunctionType

# Import from new system
from dana.registry import get_global_registry
from dana.registry.function_registry import (
    FunctionMetadata,
    RegistryAdapter,
)
from dana.registry.function_registry import (
    FunctionRegistry as NewFunctionRegistry,
)

if TYPE_CHECKING:
    pass

# Create global instance for backward compatibility
global_registry = get_global_registry()
global_function_registry = global_registry.functions

# Re-export classes
FunctionRegistry = NewFunctionRegistry

__all__ = [
    "FunctionRegistry",
    "FunctionMetadata",
    "FunctionType",
    "RegistryAdapter",
    "global_function_registry",
]
