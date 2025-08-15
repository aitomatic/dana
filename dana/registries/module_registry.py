"""
Module Registry for Dana

This module re-exports module registry functionality from the new global registry system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

# Re-export from the new global registry system
from dana.registry import (
    get_global_registry,
)

# Create convenience instances for backward compatibility
global_registry = get_global_registry()
global_module_registry = global_registry.modules

# For backward compatibility - create singleton instance
_module_registry_instance = None


def get_module_registry():
    """Get the global module registry instance (backward compatibility)."""
    global _module_registry_instance
    if _module_registry_instance is None:
        _module_registry_instance = global_registry.modules
    return _module_registry_instance


class ModuleRegistry:
    """Module registry wrapper for backward compatibility.

    This class provides the same interface as the old ModuleRegistry
    while delegating to the new ModuleRegistry.
    """

    # Singleton instance
    _instance = None

    def __new__(cls):
        """Singleton pattern for backward compatibility."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the wrapper instance."""
        if not hasattr(self, "_registry"):
            self._registry = global_registry.modules

    def register_module(self, module) -> None:
        """Register a module in the registry."""
        self._registry.register_module(module)

    def register_spec(self, spec) -> None:
        """Register a module specification."""
        self._registry.register_spec(spec)

    def get_module(self, name: str):
        """Get a module by name (raises ModuleNotFoundError if not found)."""
        return self._registry.get_module_or_raise(name)

    def get_spec(self, name: str):
        """Get a module specification by name (raises ModuleNotFoundError if not found)."""
        spec = self._registry.get_spec(name)
        if spec is None:
            from dana.core.runtime.modules.errors import ModuleNotFoundError

            raise ModuleNotFoundError(name)
        return spec

    def add_alias(self, alias: str, name: str) -> None:
        """Add a module alias."""
        self._registry.add_alias(alias, name)

    def add_dependency(self, module: str, dependency: str) -> None:
        """Add a module dependency."""
        self._registry.add_dependency(module, dependency)

    def get_dependencies(self, module: str) -> set[str]:
        """Get module dependencies."""
        return self._registry.get_dependencies(module)

    def get_loaded_modules(self) -> set[str]:
        """Get names of all loaded modules."""
        return self._registry.get_loaded_modules()

    def get_specs(self) -> set[str]:
        """Get names of all registered module specs."""
        return self._registry.get_specs()

    def get_aliases(self) -> dict[str, str]:
        """Get all module aliases."""
        return self._registry.get_aliases()

    def resolve_alias(self, alias: str) -> str:
        """Resolve a module alias to its real name."""
        return self._registry.resolve_alias(alias)

    def mark_module_loading(self, module: str) -> None:
        """Mark a module as being loaded."""
        self._registry.mark_module_loading(module)

    def mark_module_loaded(self, module: str) -> None:
        """Mark a module as loaded."""
        self._registry.mark_module_loaded(module)

    def is_module_loading(self, module: str) -> bool:
        """Check if a module is being loaded."""
        return self._registry.is_module_loading(module)

    def is_module_loaded(self, module: str) -> bool:
        """Check if a module is loaded."""
        return self._registry.is_module_loaded(module)

    def start_loading(self, module: str) -> None:
        """Start loading a module."""
        self._registry.start_loading(module)

    def finish_loading(self, module: str) -> None:
        """Finish loading a module."""
        self._registry.finish_loading(module)

    def check_circular_dependencies(self, module: str) -> None:
        """Check for circular dependencies."""
        self._registry.check_circular_dependencies_legacy(module)

    def clear(self) -> None:
        """Clear all registry state."""
        self._registry.clear_instance()


__all__ = [
    "ModuleRegistry",
    "global_module_registry",
    "get_module_registry",
]
