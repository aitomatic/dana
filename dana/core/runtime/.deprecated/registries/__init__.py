"""
DEPRECATED: Dana Core Runtime Registries

This location is deprecated. All registries have been moved to dana.registry for cleaner imports.

Please update your imports:
  OLD: from dana.core.runtime.registries import AgentTypeRegistry
  NEW: from dana.registry import TypeRegistry as AgentTypeRegistry

This module provides backward compatibility imports and will be removed in a future version.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# Backward compatibility imports from new location
import warnings

# Issue deprecation warning
warnings.warn("dana.core.runtime.registries is deprecated. Use dana.registry instead.", DeprecationWarning, stacklevel=2)

# Import all registries from new location for backward compatibility
from dana.registry import *  # noqa: F403, F401

# Re-export everything to maintain compatibility
from dana.registry import __all__  # noqa: F401
