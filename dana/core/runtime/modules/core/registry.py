"""
Dana Dana Module System - Registry

This module provides the registry for tracking Dana modules and their dependencies.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .errors import CircularImportError, ModuleNotFoundError
from .types import Module, ModuleSpec

# Global registry instance
_REGISTRY: "ModuleRegistry | None" = None


class ModuleRegistry:
    """Registry for tracking Dana modules and their dependencies."""

    def __new__(cls) -> "ModuleRegistry":
        """Create or return the singleton instance."""
        global _REGISTRY
        if _REGISTRY is None:
            _REGISTRY = super().__new__(cls)
        return _REGISTRY

    def __init__(self) -> None:
        """Initialize the registry state."""
        if not hasattr(self, "_initialized"):
            self._modules: dict[str, Module] = {}  # name -> module
            self._specs: dict[str, ModuleSpec] = {}  # name -> spec
            self._aliases: dict[str, str] = {}  # alias -> real name
            self._dependencies: dict[str, set[str]] = {}  # module -> dependencies
            self._loading: set[str] = set()  # modules being loaded
            self._initialized = True

    def clear(self) -> None:
        """Clear all registry state."""
        self._modules.clear()
        self._specs.clear()
        self._aliases.clear()
        self._dependencies.clear()
        self._loading.clear()

    def register_module(self, module: Module) -> None:
        """Register a module in the registry.

        Args:
            module: Module to register
        """
        self._modules[module.__name__] = module

    def register_spec(self, spec: ModuleSpec) -> None:
        """Register a module specification.

        Args:
            spec: Module specification to register
        """
        self._specs[spec.name] = spec

    def get_module(self, name: str) -> Module:
        """Get a module by name.

        Args:
            name: Module name or alias

        Returns:
            Module instance

        Raises:
            ModuleNotFoundError: If module not found
        """
        # Resolve alias if needed
        real_name = self._aliases.get(name, name)

        try:
            return self._modules[real_name]
        except KeyError:
            raise ModuleNotFoundError(f"Module '{name}' not found")

    def get_spec(self, name: str) -> ModuleSpec:
        """Get a module specification by name.

        Args:
            name: Module name or alias

        Returns:
            Module specification

        Raises:
            ModuleNotFoundError: If module spec not found
        """
        # Resolve alias if needed
        real_name = self._aliases.get(name, name)

        try:
            return self._specs[real_name]
        except KeyError:
            raise ModuleNotFoundError(name)

    def add_alias(self, alias: str, name: str) -> None:
        """Add a module alias.

        Args:
            alias: Alias name
            name: Real module name
        """
        self._aliases[alias] = name

    def add_dependency(self, module: str, dependency: str) -> None:
        """Add a module dependency.

        Args:
            module: Dependent module name
            dependency: Dependency module name
        """
        if module not in self._dependencies:
            self._dependencies[module] = set()
        self._dependencies[module].add(dependency)

    def get_dependencies(self, module: str) -> set[str]:
        """Get module dependencies.

        Args:
            module: Module name

        Returns:
            Set of dependency module names
        """
        return self._dependencies.get(module, set())

    def check_circular_dependencies(self, module: str) -> None:
        """Check for circular dependencies.

        Args:
            module: Module name to check

        Raises:
            CircularImportError: If circular dependency found
        """
        visited = set()
        path = []
        self._check_circular_dependencies(module, visited, path)

    def _check_circular_dependencies(self, module: str, visited: set[str], path: list[str]) -> None:
        """Internal implementation of circular dependency check.

        Args:
            module: Module name to check
            visited: Set of visited modules
            path: Current dependency path

        Raises:
            CircularImportError: If circular dependency found
        """
        if module in visited:
            # Found a cycle, get the cycle path
            cycle_start = path.index(module)
            cycle = path[cycle_start:] + [module]
            raise CircularImportError(cycle)

        visited.add(module)
        path.append(module)

        for dep in self.get_dependencies(module):
            self._check_circular_dependencies(dep, visited, path)

        path.pop()

    def mark_module_loading(self, name: str) -> None:
        """Mark a module as being loaded.

        Args:
            name: Module name
        """
        self._loading.add(name)

    def mark_module_loaded(self, name: str) -> None:
        """Mark a module as loaded.

        Args:
            name: Module name
        """
        self._loading.discard(name)

    def start_loading(self, name: str) -> None:
        """Start loading a module.

        Args:
            name: Module name
        """
        self.mark_module_loading(name)

    def finish_loading(self, name: str) -> None:
        """Finish loading a module.

        Args:
            name: Module name
        """
        self.mark_module_loaded(name)

    def is_module_loading(self, name: str) -> bool:
        """Check if a module is being loaded.

        Args:
            name: Module name

        Returns:
            True if module is being loaded
        """
        return name in self._loading

    def is_module_loaded(self, name: str) -> bool:
        """Check if a module is loaded.

        Args:
            name: Module name

        Returns:
            True if module is loaded
        """
        return name in self._modules

    def get_loaded_modules(self) -> set[str]:
        """Get names of all loaded modules.

        Returns:
            Set of module names
        """
        return set(self._modules.keys())

    def get_specs(self) -> set[str]:
        """Get names of all registered module specs.

        Returns:
            Set of module names
        """
        return set(self._specs.keys())

    def get_aliases(self) -> dict[str, str]:
        """Get all module aliases.

        Returns:
            Dictionary mapping alias names to real names
        """
        return self._aliases.copy()

    def resolve_alias(self, alias: str) -> str:
        """Resolve a module alias to its real name.

        Args:
            alias: Alias name

        Returns:
            Real module name
        """
        return self._aliases.get(alias, alias)
