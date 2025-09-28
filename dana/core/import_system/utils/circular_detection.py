"""
Circular import detection and handling.

Provides intelligent circular import detection that distinguishes between
legitimate circular imports (that Python allows) and problematic ones.
"""

from typing import List, Set, Dict, Optional
from collections import defaultdict


class CircularImportDetector:
    """Detects and handles circular imports intelligently."""

    def __init__(self):
        """Initialize the circular import detector."""
        self._loading_modules: Set[str] = set()
        self._module_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._allowable_patterns: Set[str] = set()

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

    def is_loading(self, module_name: str) -> bool:
        """Check if a module is currently loading.

        Args:
            module_name: The name of the module to check

        Returns:
            True if the module is currently loading
        """
        return module_name in self._loading_modules

    def add_dependency(self, from_module: str, to_module: str) -> None:
        """Add a dependency relationship between modules.

        Args:
            from_module: The module that depends on another
            to_module: The module being depended upon
        """
        self._module_dependencies[from_module].add(to_module)

    def check_circular_import(self, module_name: str, importing_from: str) -> bool:
        """Check if importing a module would create a circular import.

        Args:
            module_name: The module being imported
            importing_from: The module doing the import

        Returns:
            True if this would create a problematic circular import
        """
        if not self.is_loading(module_name):
            return False

        # Check if this is an allowable circular import pattern
        if self._is_allowable_circular_import(module_name, importing_from):
            return False

        # Check for actual circular dependency
        return self._has_circular_dependency(importing_from, module_name)

    def _is_allowable_circular_import(self, module_name: str, importing_from: str) -> bool:
        """Check if a circular import is allowable (Python-compatible).

        Args:
            module_name: The module being imported
            importing_from: The module doing the import

        Returns:
            True if this circular import should be allowed
        """
        # Allow circular imports within the same package
        if '.' in module_name and '.' in importing_from:
            module_package = module_name.rsplit('.', 1)[0]
            importing_package = importing_from.rsplit('.', 1)[0]
            if module_package == importing_package:
                return True

        # Allow submodules to import from their parent package
        if '.' in importing_from:
            importing_package = importing_from.rsplit('.', 1)[0]
            if module_name == importing_package:
                return True

        # Allow sibling submodules to cross-reference
        if ('.' in module_name and '.' in importing_from and
            module_name.count('.') == importing_from.count('.') and
            module_name.rsplit('.', 1)[0] == importing_from.rsplit('.', 1)[0]):
            return True

        return False

    def _has_circular_dependency(self, from_module: str, to_module: str) -> bool:
        """Check if there's a circular dependency between modules.

        Args:
            from_module: The module that depends on another
            to_module: The module being depended upon

        Returns:
            True if there's a circular dependency
        """
        visited = set()
        return self._dfs_check_cycle(to_module, from_module, visited)

    def _dfs_check_cycle(self, current: str, target: str, visited: Set[str]) -> bool:
        """Depth-first search to check for cycles.

        Args:
            current: Current module being checked
            target: Target module to find
            visited: Set of visited modules

        Returns:
            True if a cycle is found
        """
        if current == target:
            return True

        if current in visited:
            return False

        visited.add(current)

        for dependency in self._module_dependencies.get(current, set()):
            if self._dfs_check_cycle(dependency, target, visited):
                return True

        return False

    def get_loading_chain(self, module_name: str) -> List[str]:
        """Get the current loading chain for a module.

        Args:
            module_name: The module to get the loading chain for

        Returns:
            List of modules in the loading chain
        """
        return list(self._loading_modules)

    def clear_dependencies(self, module_name: str) -> None:
        """Clear dependencies for a module.

        Args:
            module_name: The module to clear dependencies for
        """
        self._module_dependencies.pop(module_name, None)
        for deps in self._module_dependencies.values():
            deps.discard(module_name)



