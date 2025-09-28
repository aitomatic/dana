"""
Module resolution logic.

Handles the discovery and resolution of modules in the import system.
This includes finding modules in search paths, resolving relative imports,
and determining module types (Dana vs Python).
"""

from typing import Optional, List, Tuple
from pathlib import Path
import sys


class ModuleResolver:
    """Resolves module names to file paths and determines module types."""

    def __init__(self, search_paths: Optional[List[Path]] = None):
        """Initialize the module resolver.

        Args:
            search_paths: Custom search paths for module discovery
        """
        self.search_paths = search_paths or [Path(p) for p in sys.path if Path(p).exists()]

    def resolve_module(self, module_name: str, current_file: Optional[Path] = None) -> Tuple[Optional[Path], str]:
        """Resolve a module name to a file path.

        Args:
            module_name: The module name to resolve
            current_file: The current file context for relative imports

        Returns:
            Tuple of (file_path, module_type) where module_type is 'dana' or 'python'
        """
        # Handle relative imports
        if module_name.startswith('.'):
            return self._resolve_relative_import(module_name, current_file)

        # Handle absolute imports
        return self._resolve_absolute_import(module_name)

    def _resolve_relative_import(self, module_name: str, current_file: Optional[Path]) -> Tuple[Optional[Path], str]:
        """Resolve a relative import.

        Args:
            module_name: The relative module name (e.g., '.submodule', '..parent')
            current_file: The current file context

        Returns:
            Tuple of (file_path, module_type)
        """
        if not current_file:
            raise ImportError(f"Relative import '{module_name}' attempted without package context")

        # Calculate the target path based on relative import
        current_dir = current_file.parent
        parts = module_name.split('.')

        # Remove leading dots and navigate up directories
        up_levels = len([p for p in parts if p == ''])
        target_name = parts[-1] if parts[-1] else '__init__'

        # Navigate up the directory structure
        target_dir = current_dir
        for _ in range(up_levels - 1):
            target_dir = target_dir.parent

        # Look for the target module
        return self._find_module_in_directory(target_dir, target_name)

    def _resolve_absolute_import(self, module_name: str) -> Tuple[Optional[Path], str]:
        """Resolve an absolute import.

        Args:
            module_name: The absolute module name

        Returns:
            Tuple of (file_path, module_type)
        """
        # Search in all search paths
        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            # Convert module name to file path
            module_path = search_path / module_name.replace('.', '/')

            # Try to find the module
            result = self._find_module_in_directory(module_path.parent, module_path.name)
            if result[0]:
                return result

        return None, 'unknown'

    def _find_module_in_directory(self, directory: Path, name: str) -> Tuple[Optional[Path], str]:
        """Find a module in a specific directory.

        Args:
            directory: The directory to search in
            name: The module name to find

        Returns:
            Tuple of (file_path, module_type)
        """
        if not directory.exists():
            return None, 'unknown'

        # Try Dana module first (.na file)
        dana_file = directory / f"{name}.na"
        if dana_file.exists():
            return dana_file, 'dana'

        # Try Python module (.py file)
        python_file = directory / f"{name}.py"
        if python_file.exists():
            return python_file, 'python'

        # Try package directory
        package_dir = directory / name
        if package_dir.is_dir():
            # Check for __init__.na first
            init_na = package_dir / "__init__.na"
            if init_na.exists():
                return init_na, 'dana'

            # Check for __init__.py
            init_py = package_dir / "__init__.py"
            if init_py.exists():
                return init_py, 'python'

            # Namespace package (no __init__ file)
            return package_dir, 'namespace'

        return None, 'unknown'
