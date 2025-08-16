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

import sys
import warnings
from pathlib import Path

# Add the deprecated directory to the path so we can import from it
deprecated_path = Path(__file__).parent.parent / ".deprecated" / "registries"
if deprecated_path.exists():
    sys.path.insert(0, str(deprecated_path.parent.parent))

warnings.warn(
    "dana.registries.function_registry is deprecated. Please use dana.registry.function_registry instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Import from the deprecated module
try:
    from .deprecated.registries.function_registry import *
except ImportError:
    # Fallback to direct import if the path structure doesn't work
    import sys

    sys.path.insert(0, str(Path(__file__).parent / ".deprecated"))
    from registries.function_registry import *
