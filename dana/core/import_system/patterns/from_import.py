"""
From-import statement handling.

Handles `from module import name` and `from module import name as alias` patterns
with proper lazy loading and circular import detection.
"""

from typing import List, Tuple, Any, Optional, Dict
from ..core.lazy_loader import LazyLoader
from ..utils.circular_detection import CircularImportDetector


class FromImportHandler:
    """Handles from-import statements with lazy loading support."""

    def __init__(self, circular_detector: CircularImportDetector):
        """Initialize the from-import handler.

        Args:
            circular_detector: The circular import detector to use
        """
        self.circular_detector = circular_detector

    def handle_from_import(self,
                          module_name: str,
                          names: List[Tuple[str, Optional[str]]],
                          current_module: str) -> Dict[str, Any]:
        """Handle a from-import statement.

        Args:
            module_name: The module to import from
            names: List of (name, alias) tuples to import
            current_module: The current module doing the import

        Returns:
            Dictionary of imported names and their values
        """
        # Check for circular import
        if self.circular_detector.check_circular_import(module_name, current_module):
            # Handle circular import gracefully
            return self._handle_circular_import(module_name, names, current_module)

        # Try to get the module
        try:
            module = self._get_module(module_name, current_module)
            return self._extract_names_from_module(module, names, module_name)
        except Exception as e:
            # If module loading fails, try lazy loading
            return self._handle_lazy_loading(module_name, names, current_module, e)

    def _handle_circular_import(self,
                               module_name: str,
                               names: List[Tuple[str, Optional[str]]],
                               current_module: str) -> Dict[str, Any]:
        """Handle a circular import by using lazy loading.

        Args:
            module_name: The module being imported
            names: List of names to import
            current_module: The current module

        Returns:
            Dictionary of lazy-loaded names
        """
        result = {}

        for name, alias in names:
            target_name = alias or name

            # Create a lazy loader for this name
            def create_lazy_loader():
                def lazy_loader():
                    module = self._get_module(module_name, current_module)
                    return getattr(module, name)
                return lazy_loader

            result[target_name] = LazyLoader.create_lazy_loader(
                f"{module_name}.{name}",
                create_lazy_loader()
            )

        return result

    def _handle_lazy_loading(self,
                           module_name: str,
                           names: List[Tuple[str, Optional[str]]],
                           current_module: str,
                           error: Exception) -> Dict[str, Any]:
        """Handle lazy loading when module loading fails.

        Args:
            module_name: The module being imported
            names: List of names to import
            current_module: The current module
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
                        module = self._get_module(module_name, current_module)
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

    def _get_module(self, module_name: str, current_module: str) -> Any:
        """Get a module by name.

        Args:
            module_name: The module name
            current_module: The current module context

        Returns:
            The loaded module
        """
        # This would integrate with the actual module loading system
        # For now, this is a placeholder
        raise NotImplementedError("Module loading integration needed")

    def _extract_names_from_module(self,
                                 module: Any,
                                 names: List[Tuple[str, Optional[str]]],
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
