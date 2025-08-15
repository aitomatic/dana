"""
DEPRECATED: Unified Function Registry for Dana and Python functions.

This module has been moved to dana.core.runtime.registries.function_registry.
Please update your imports accordingly.

This module now provides backward compatibility imports only.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# Backward compatibility imports - import everything from the new location
# For any modules that still import from the old location, keep the preloaded functions functionality
import dana.registry.function_registry as new_module

# Initialize _preloaded_functions for backward compatibility
_preloaded_functions = {}

# Store a reference to preserve the old module's _preloaded_functions if it exists
if hasattr(globals(), "_preloaded_functions"):
    new_module._preloaded_functions = globals()["_preloaded_functions"]

# Explicit imports to avoid F405 errors
# Import FunctionType from the correct location
from dana.core.lang.interpreter.executor.function_resolver import FunctionType
from dana.registry.function_registry import (
    FunctionMetadata,
    FunctionRegistry,
    RegistryAdapter,
)

# For backward compatibility, create PreloadedFunctionRegistry alias
PreloadedFunctionRegistry = FunctionRegistry

# Re-export everything to maintain compatibility
__all__ = [
    "FunctionRegistry",
    "FunctionMetadata",
    "FunctionType",
    "RegistryAdapter",
    "PreloadedFunctionRegistry",
    "_preloaded_functions",
]
