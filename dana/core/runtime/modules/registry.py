"""
DEPRECATED: Dana Module System - Registry

This module has been moved to dana.core.runtime.registries.module_registry.
Please update your imports accordingly.

This module now provides backward compatibility imports only.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# Backward compatibility imports
from dana.registries.module_registry import ModuleRegistry

# Re-export for backward compatibility
__all__ = ["ModuleRegistry"]
