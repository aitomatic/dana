"""
Module Registry for Dana

Specialized registry for module loading and dependency tracking.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any


class ModuleRegistry:
    """Registry for tracking Dana modules and their dependencies.

    This registry uses complex multi-storage to track modules, specifications,
    aliases, dependencies, and loading states.
    """

    def __init__(self):
        """Initialize the module registry with complex multi-storage."""
        # Module storage
        self._modules: dict[str, Any] = {}  # name -> module

        # Module specifications
        self._specs: dict[str, Any] = {}  # name -> spec

        # Module aliases
        self._aliases: dict[str, str] = {}  # alias -> real_name

        # Module dependencies
        self._dependencies: dict[str, set[str]] = {}  # module -> dependencies

        # Modules being loaded (to detect circular dependencies)
        self._loading: set[str] = set()

        # Module lifecycle tracking
        self._load_order: list[str] = []
        self._load_times: dict[str, float] = {}

        # Module metadata
        self._module_metadata: dict[str, dict[str, Any]] = {}

    def register_module(self, module: Any) -> None:
        """Register a module in the registry.

        Args:
            module: Module to register
        """
        if not hasattr(module, "__name__"):
            raise ValueError("Module must have a '__name__' attribute")

        name = module.__name__
        self._modules[name] = module
        self._module_metadata[name] = {
            "registered_at": self._get_timestamp(),
            "type": "module",
        }

        if name not in self._load_order:
            self._load_order.append(name)

    def register_spec(self, spec: Any) -> None:
        """Register a module specification.

        Args:
            spec: Module specification to register
        """
        if not hasattr(spec, "name"):
            raise ValueError("Module spec must have a 'name' attribute")

        name = spec.name
        self._specs[name] = spec
        self._module_metadata[name] = {
            "registered_at": self._get_timestamp(),
            "type": "spec",
        }

    def register_alias(self, alias: str, real_name: str) -> None:
        """Register a module alias.

        Args:
            alias: The alias name
            real_name: The real module name
        """
        self._aliases[alias] = real_name

    def register_dependency(self, module: str, dependency: str) -> None:
        """Register a dependency between modules.

        Args:
            module: The module that depends on the dependency
            dependency: The module being depended on
        """
        if module not in self._dependencies:
            self._dependencies[module] = set()
        self._dependencies[module].add(dependency)

    def get_module(self, name: str) -> Any | None:
        """Get a module by name (handles aliases).

        Args:
            name: The module name or alias

        Returns:
            The module or None if not found
        """
        # Check if it's an alias
        real_name = self._aliases.get(name, name)
        return self._modules.get(real_name)

    def get_module_or_raise(self, name: str) -> Any:
        """Get a module by name or raise ModuleNotFoundError (backward compatibility).

        Args:
            name: The module name or alias

        Returns:
            The module

        Raises:
            ModuleNotFoundError: If module not found
        """
        module = self.get_module(name)
        if module is None:
            # Import here to avoid circular imports
            from dana.core.runtime.modules.errors import ModuleNotFoundError

            raise ModuleNotFoundError(f"Module '{name}' not found")
        return module

    def get_spec(self, name: str) -> Any | None:
        """Get a module specification by name.

        Args:
            name: The module name

        Returns:
            The module spec or None if not found
        """
        return self._specs.get(name)

    def get_real_name(self, alias: str) -> str | None:
        """Get the real name for an alias.

        Args:
            alias: The alias name

        Returns:
            The real name or None if not found
        """
        return self._aliases.get(alias)

    def get_dependencies(self, module: str) -> set[str]:
        """Get dependencies for a module.

        Args:
            module: The module name

        Returns:
            Set of dependency names
        """
        return self._dependencies.get(module, set()).copy()

    def get_dependents(self, module: str) -> set[str]:
        """Get modules that depend on the given module.

        Args:
            module: The module name

        Returns:
            Set of dependent module names
        """
        dependents = set()
        for dependent, deps in self._dependencies.items():
            if module in deps:
                dependents.add(dependent)
        return dependents

    def list_modules(self) -> list[str]:
        """List all registered module names.

        Returns:
            List of module names in load order
        """
        return self._load_order.copy()

    def list_specs(self) -> list[str]:
        """List all registered module specification names.

        Returns:
            List of module spec names
        """
        return list(self._specs.keys())

    def list_aliases(self) -> list[str]:
        """List all registered module aliases.

        Returns:
            List of alias names
        """
        return list(self._aliases.keys())

    def list_dependencies(self) -> dict[str, set[str]]:
        """List all module dependencies.

        Returns:
            Dictionary of module names to dependency sets
        """
        return {module: deps.copy() for module, deps in self._dependencies.items()}

    def is_loading(self, module: str) -> bool:
        """Check if a module is currently being loaded.

        Args:
            module: The module name

        Returns:
            True if the module is being loaded
        """
        return module in self._loading

    def mark_loading(self, module: str) -> None:
        """Mark a module as being loaded.

        Args:
            module: The module name
        """
        self._loading.add(module)

    def mark_loaded(self, module: str) -> None:
        """Mark a module as loaded.

        Args:
            module: The module name
        """
        self._loading.discard(module)
        if module not in self._load_times:
            self._load_times[module] = self._get_timestamp()

    def get_load_time(self, module: str) -> float | None:
        """Get the load time for a module.

        Args:
            module: The module name

        Returns:
            Load timestamp or None if not loaded
        """
        return self._load_times.get(module)

    def get_module_metadata(self, name: str) -> dict[str, Any] | None:
        """Get metadata for a module.

        Args:
            name: The module name

        Returns:
            Module metadata or None if not found
        """
        return self._module_metadata.get(name)

    def check_circular_dependencies(self, module: str, visited: set[str] | None = None, path: list[str] | None = None) -> list[str]:
        """Check for circular dependencies starting from a module.

        Args:
            module: The module to check
            visited: Set of visited modules (for recursion)
            path: Current dependency path (for recursion)

        Returns:
            List of modules in the circular dependency cycle, or empty list if none
        """
        if visited is None:
            visited = set()
        if path is None:
            path = []

        if module in visited:
            # Found a cycle
            cycle_start = path.index(module)
            cycle = path[cycle_start:] + [module]
            return cycle

        visited.add(module)
        path.append(module)

        for dep in self.get_dependencies(module):
            cycle = self.check_circular_dependencies(dep, visited.copy(), path.copy())
            if cycle:
                return cycle

        return []

    def get_load_order(self) -> list[str]:
        """Get the order in which modules were loaded.

        Returns:
            List of module names in load order
        """
        return self._load_order.copy()

    def clear_instance(self) -> None:
        """Clear all registry state (for testing)."""
        self._modules.clear()
        self._specs.clear()
        self._aliases.clear()
        self._dependencies.clear()
        self._loading.clear()
        self._load_order.clear()
        self._load_times.clear()
        self._module_metadata.clear()

    @classmethod
    def clear(cls) -> None:
        """Clear all registry state (backward compatibility for testing)."""
        from dana.registry import MODULE_REGISTRY

        MODULE_REGISTRY.clear_instance()

    def count(self) -> int:
        """Get the total number of registered modules."""
        return len(self._modules)

    def is_empty(self) -> bool:
        """Check if the registry is empty."""
        return len(self._modules) == 0

    # Backward compatibility methods
    def start_loading(self, module: str) -> None:
        """Start loading a module (backward compatibility).

        Args:
            module: The module name
        """
        self.mark_loading(module)

    def finish_loading(self, module: str) -> None:
        """Finish loading a module (backward compatibility).

        Args:
            module: The module name
        """
        self.mark_loaded(module)

    def is_module_loading(self, module: str) -> bool:
        """Check if a module is being loaded (backward compatibility).

        Args:
            module: The module name

        Returns:
            True if the module is being loaded
        """
        return self.is_loading(module)

    def is_module_loaded(self, module: str) -> bool:
        """Check if a module is loaded (backward compatibility).

        Args:
            module: The module name

        Returns:
            True if the module is loaded
        """
        return module in self._modules

    def get_loaded_modules(self) -> set[str]:
        """Get names of all loaded modules (backward compatibility).

        Returns:
            Set of module names
        """
        return set(self._modules.keys())

    def get_specs(self) -> set[str]:
        """Get names of all registered module specs (backward compatibility).

        Returns:
            Set of module spec names
        """
        return set(self._specs.keys())

    def get_aliases(self) -> dict[str, str]:
        """Get all module aliases (backward compatibility).

        Returns:
            Dictionary mapping alias names to real names
        """
        return self._aliases.copy()

    def mark_module_loading(self, module: str) -> None:
        """Mark a module as being loaded (backward compatibility).

        Args:
            module: The module name
        """
        self.mark_loading(module)

    def mark_module_loaded(self, module: str) -> None:
        """Mark a module as loaded (backward compatibility).

        Args:
            module: The module name
        """
        self.mark_loaded(module)

    def resolve_alias(self, alias: str) -> str:
        """Resolve a module alias to its real name (backward compatibility).

        Args:
            alias: Alias name

        Returns:
            Real module name
        """
        return self._aliases.get(alias, alias)

    def add_alias(self, alias: str, name: str) -> None:
        """Add a module alias (backward compatibility).

        Args:
            alias: Alias name
            name: Real module name
        """
        self.register_alias(alias, name)

    def add_dependency(self, module: str, dependency: str) -> None:
        """Add a module dependency (backward compatibility).

        Args:
            module: Dependent module name
            dependency: Dependency module name
        """
        self.register_dependency(module, dependency)

    def check_circular_dependencies_legacy(self, module: str) -> None:
        """Check for circular dependencies (backward compatibility).

        Args:
            module: Module name to check

        Raises:
            CircularImportError: If circular dependency found
        """
        cycle = self.check_circular_dependencies(module)
        if cycle:
            # Import here to avoid circular imports
            from dana.core.runtime.modules.errors import CircularImportError

            raise CircularImportError(cycle)

    def _check_circular_dependencies(self, module: str, visited: set[str], path: list[str]) -> None:
        """Internal implementation of circular dependency check (backward compatibility).

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
            # Import here to avoid circular imports
            from dana.core.runtime.modules.errors import CircularImportError

            raise CircularImportError(cycle)

        visited.add(module)
        path.append(module)

        for dep in self.get_dependencies(module):
            self._check_circular_dependencies(dep, visited, path)

        path.pop()

    def _get_timestamp(self) -> float:
        """Get current timestamp for tracking."""
        import time

        return time.time()

    def __repr__(self) -> str:
        """String representation of the module registry."""
        return (
            f"ModuleRegistry("
            f"modules={len(self._modules)}, "
            f"specs={len(self._specs)}, "
            f"aliases={len(self._aliases)}, "
            f"dependencies={len(self._dependencies)}, "
            f"loading={len(self._loading)}"
            f")"
        )
