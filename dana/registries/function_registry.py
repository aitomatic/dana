"""
Function Registry for Dana - BACKWARD COMPATIBILITY LAYER

This module now re-exports from the new global registry system.
The original implementation has been migrated to dana.registry.function_registry.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

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
