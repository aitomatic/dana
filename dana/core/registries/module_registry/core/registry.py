"""
Module registry and caching.

Manages the registry of loaded modules, their dependencies, and provides
caching and lifecycle management for the importing system.
"""

from typing import Dict, Set, Optional, Any
from collections import defaultdict


class ModuleRegistry:
    """Registry for managing loaded modules and their dependencies."""

    def __init__(self):
        """Initialize the module registry."""
        self._modules: Dict[str, Any] = {}
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._loading_modules: Set[str] = set()

    def register_module(self, module_name: str, module: Any) -> None:
        """Register a loaded module.

        Args:
            module_name: The name of the module
            module: The loaded module object
        """
        self._modules[module_name] = module

    def get_module(self, module_name: str) -> Optional[Any]:
        """Get a registered module.

        Args:
            module_name: The name of the module

        Returns:
            The module or None if not registered
        """
        return self._modules.get(module_name)

    def is_module_registered(self, module_name: str) -> bool:
        """Check if a module is registered.

        Args:
            module_name: The name of the module

        Returns:
            True if the module is registered
        """
        return module_name in self._modules

    def start_loading(self, module_name: str) -> None:
        """Mark a module as currently loading.

        Args:
            module_name: The name of the module being loaded
        """
        self._loading_modules.add(module_name)

    def finish_loading(self, module_name: str) -> None:
        """Mark a module as finished loading.

        Args:
            module_name: The name of the module that finished loading
        """
        self._loading_modules.discard(module_name)

    def is_module_loading(self, module_name: str) -> bool:
        """Check if a module is currently loading.

        Args:
            module_name: The name of the module

        Returns:
            True if the module is currently loading
        """
        return module_name in self._loading_modules

    def add_dependency(self, from_module: str, to_module: str) -> None:
        """Add a dependency relationship.

        Args:
            from_module: The module that depends on another
            to_module: The module being depended upon
        """
        self._dependencies[from_module].add(to_module)
        self._reverse_dependencies[to_module].add(from_module)

    def get_dependencies(self, module_name: str) -> Set[str]:
        """Get the dependencies of a module.

        Args:
            module_name: The name of the module

        Returns:
            Set of module names that this module depends on
        """
        return self._dependencies.get(module_name, set()).copy()

    def get_dependents(self, module_name: str) -> Set[str]:
        """Get the modules that depend on this module.

        Args:
            module_name: The name of the module

        Returns:
            Set of module names that depend on this module
        """
        return self._reverse_dependencies.get(module_name, set()).copy()

    def remove_module(self, module_name: str) -> None:
        """Remove a module from the registry.

        Args:
            module_name: The name of the module to remove
        """
        self._modules.pop(module_name, None)
        self._dependencies.pop(module_name, None)

        # Remove from reverse dependencies
        for deps in self._reverse_dependencies.values():
            deps.discard(module_name)

    def clear_dependencies(self, module_name: str) -> None:
        """Clear all dependencies for a module.

        Args:
            module_name: The name of the module
        """
        # Remove from forward dependencies
        deps = self._dependencies.pop(module_name, set())

        # Remove from reverse dependencies
        for dep in deps:
            self._reverse_dependencies[dep].discard(module_name)

    def get_loading_chain(self) -> Set[str]:
        """Get the current loading chain.

        Returns:
            Set of module names currently being loaded
        """
        return self._loading_modules.copy()

    def get_all_modules(self) -> Dict[str, Any]:
        """Get all registered modules.

        Returns:
            Dictionary of all registered modules
        """
        return self._modules.copy()

    def clear(self) -> None:
        """Clear the entire registry."""
        self._modules.clear()
        self._dependencies.clear()
        self._reverse_dependencies.clear()
        self._loading_modules.clear()



