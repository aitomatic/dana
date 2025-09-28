"""
Unified Import Handler.

This is the main entry point for the unified importing system.
It coordinates all the components to provide consistent, Python-compatible
import behavior for Dana modules.
"""

from typing import Any, Optional, Dict, List, Tuple
from pathlib import Path
import sys

from .core.resolver import ModuleResolver
from .core.loader import ModuleLoader
from .core.registry import ModuleRegistry
from .core.lazy_loader import LazyLoader
from .utils.circular_detection import CircularImportDetector
from .patterns.from_import import FromImportHandler


class UnifiedImportHandler:
    """Main handler for all import operations in the unified system."""

    def __init__(self, search_paths: Optional[List[Path]] = None):
        """Initialize the unified import handler.

        Args:
            search_paths: Custom search paths for module discovery
        """
        self.resolver = ModuleResolver(search_paths)
        self.loader = ModuleLoader()
        self.registry = ModuleRegistry()
        self.circular_detector = CircularImportDetector()
        self.from_import_handler = FromImportHandler(self.circular_detector)

        # Add current directory to search paths if not already there
        current_dir = Path.cwd()
        if current_dir not in self.resolver.search_paths:
            self.resolver.search_paths.insert(0, current_dir)

    def import_module(self, module_name: str, current_file: Optional[Path] = None) -> Any:
        """Import a module by name.

        Args:
            module_name: The name of the module to import
            current_file: The current file context for relative imports

        Returns:
            The imported module
        """
        # Check if already loaded
        if self.registry.is_module_registered(module_name):
            return self.registry.get_module(module_name)

        # Check for circular import
        if self.circular_detector.check_circular_import(module_name, str(current_file) if current_file else ""):
            # Handle circular import with lazy loading
            return self._handle_circular_import(module_name, current_file)

        # Resolve the module
        file_path, module_type = self.resolver.resolve_module(module_name, current_file)
        if not file_path:
            raise ImportError(f"No module named '{module_name}'")

        # Start loading
        self.registry.start_loading(module_name)
        self.circular_detector.start_loading(module_name)

        try:
            # Load the module
            module = self.loader.load_module(module_name, file_path, module_type)

            # Register the module
            self.registry.register_module(module_name, module)

            # Handle submodules for packages
            if module_type in ['dana', 'python'] and file_path.is_dir():
                self._populate_package_submodules(module, module_name, file_path)

            return module

        finally:
            self.registry.finish_loading(module_name)
            self.circular_detector.finish_loading(module_name)

    def from_import(self, module_name: str, names: List[Tuple[str, Optional[str]]],
                   current_file: Optional[Path] = None) -> Dict[str, Any]:
        """Handle from-import statements.

        Args:
            module_name: The module to import from
            names: List of (name, alias) tuples to import
            current_file: The current file context

        Returns:
            Dictionary of imported names and their values
        """
        # First try to get the module
        try:
            module = self.import_module(module_name, current_file)
            return self._extract_names_from_module(module, names, module_name)
        except Exception as e:
            # If module loading fails, try lazy loading
            return self._handle_lazy_from_import(module_name, names, current_file, e)

    def _handle_circular_import(self, module_name: str, current_file: Optional[Path]) -> Any:
        """Handle circular import by creating a lazy loader.

        Args:
            module_name: The module name
            current_file: The current file context

        Returns:
            A lazy loader for the module
        """
        def create_lazy_loader():
            def lazy_loader():
                return self.import_module(module_name, current_file)
            return lazy_loader

        return LazyLoader.create_lazy_loader(module_name, create_lazy_loader())

    def _handle_lazy_from_import(self, module_name: str, names: List[Tuple[str, Optional[str]]],
                                current_file: Optional[Path], error: Exception) -> Dict[str, Any]:
        """Handle lazy loading for from-import when module loading fails.

        Args:
            module_name: The module name
            names: List of names to import
            current_file: The current file context
            error: The original loading error

        Returns:
            Dictionary of lazy-loaded names
        """
        result = {}

        for name, alias in names:
            target_name = alias or name

            # Create a lazy loader that will retry loading
            def create_retry_lazy_loader():
                def lazy_loader():
                    try:
                        module = self.import_module(module_name, current_file)
                        return getattr(module, name)
                    except Exception:
                        # If it still fails, raise the original error
                        raise error
                return lazy_loader

            result[target_name] = LazyLoader.create_lazy_loader(
                f"{module_name}.{name}",
                create_retry_lazy_loader()
            )

        return result

    def _extract_names_from_module(self, module: Any, names: List[Tuple[str, Optional[str]]],
                                  module_name: str) -> Dict[str, Any]:
        """Extract names from a loaded module.

        Args:
            module: The loaded module
            names: List of names to extract
            module_name: The module name for error reporting

        Returns:
            Dictionary of extracted names
        """
        result = {}

        for name, alias in names:
            target_name = alias or name

            try:
                value = getattr(module, name)

                # Check if this is a lazy loader and resolve it
                if LazyLoader.is_lazy_loader(value):
                    value = LazyLoader.resolve_lazy_loader(value)

                result[target_name] = value

            except AttributeError:
                # Check if this might be a lazy loader that needs resolution
                if hasattr(module, name):
                    attr = getattr(module, name)
                    if LazyLoader.is_lazy_loader(attr):
                        result[target_name] = LazyLoader.resolve_lazy_loader(attr)
                    else:
                        raise AttributeError(f"module '{module_name}' has no attribute '{name}'")
                else:
                    raise AttributeError(f"module '{module_name}' has no attribute '{name}'")

        return result

    def _populate_package_submodules(self, module: Any, module_name: str, package_path: Path) -> None:
        """Populate a package with its submodules using lazy loading.

        Args:
            module: The package module
            module_name: The package name
            package_path: The path to the package directory
        """
        if not package_path.is_dir():
            return

        # Find all submodules
        for item in package_path.iterdir():
            if item.is_file() and item.suffix in ['.na', '.py']:
                submodule_name = item.stem
                if submodule_name == '__init__':
                    continue

                full_submodule_name = f"{module_name}.{submodule_name}"

                # Create lazy loader for submodule
                def create_submodule_lazy_loader():
                    def lazy_loader():
                        return self.import_module(full_submodule_name)
                    return lazy_loader

                lazy_loader = LazyLoader.create_lazy_loader(full_submodule_name, create_submodule_lazy_loader())
                setattr(module, submodule_name, lazy_loader)

            elif item.is_dir() and not (item / '__init__.na').exists() and not (item / '__init__.py').exists():
                # Namespace package subdirectory
                submodule_name = item.name
                full_submodule_name = f"{module_name}.{submodule_name}"

                # Create lazy loader for namespace submodule
                def create_namespace_lazy_loader():
                    def lazy_loader():
                        return self.import_module(full_submodule_name)
                    return lazy_loader

                lazy_loader = LazyLoader.create_lazy_loader(full_submodule_name, create_namespace_lazy_loader())
                setattr(module, submodule_name, lazy_loader)

    def get_module_info(self, module_name: str) -> Dict[str, Any]:
        """Get information about a module.

        Args:
            module_name: The module name

        Returns:
            Dictionary with module information
        """
        return {
            'name': module_name,
            'is_loaded': self.registry.is_module_registered(module_name),
            'is_loading': self.registry.is_module_loading(module_name),
            'dependencies': self.registry.get_dependencies(module_name),
            'dependents': self.registry.get_dependents(module_name),
        }

    def clear_cache(self) -> None:
        """Clear all cached modules and reset the system."""
        self.registry.clear()
        self.loader._loaded_modules.clear()
        self.loader._loading_modules.clear()
        self.circular_detector._loading_modules.clear()



