"""
Lazy loading mechanism.

Handles the creation and resolution of lazy loaders for submodules,
preventing circular import issues while maintaining Python-compatible behavior.
"""

from typing import Callable, Any, Optional
from pathlib import Path
import sys


class LazyLoader:
    """Manages lazy loading of submodules to prevent circular imports."""

    def __init__(self, module_name: str, loader_func: Callable[[], Any]):
        """Initialize a lazy loader.

        Args:
            module_name: The name of the module to load lazily
            loader_func: Function that loads the actual module
        """
        self.module_name = module_name
        self._loader_func = loader_func
        self._loaded_module: Optional[Any] = None
        self._loading = False

    def __call__(self) -> Any:
        """Load the module if not already loaded.

        Returns:
            The loaded module
        """
        if self._loaded_module is not None:
            return self._loaded_module

        if self._loading:
            # Circular import detected, return a placeholder
            return self._create_placeholder()

        self._loading = True
        try:
            self._loaded_module = self._loader_func()
            return self._loaded_module
        except Exception as e:
            # If loading fails, return a placeholder that will retry
            return self._create_placeholder_with_error(e)
        finally:
            self._loading = False

    def _create_placeholder(self) -> Any:
        """Create a placeholder module for circular import situations.

        Returns:
            A placeholder module object
        """
        class PlaceholderModule:
            def __init__(self, name: str):
                self.__name__ = name
                self.__file__ = None
                self.__package__ = name.rsplit('.', 1)[0] if '.' in name else None

            def __getattr__(self, name: str) -> Any:
                # Try to load the actual module when accessed
                try:
                    actual_module = self._load_actual_module()
                    return getattr(actual_module, name)
                except Exception:
                    raise AttributeError(f"module '{self.__name__}' has no attribute '{name}'")

            def _load_actual_module(self) -> Any:
                # This will be called when the module is actually accessed
                return LazyLoader.this._loader_func()

        placeholder = PlaceholderModule(self.module_name)
        LazyLoader.this = self  # Store reference for the placeholder
        return placeholder

    def _create_placeholder_with_error(self, error: Exception) -> Any:
        """Create a placeholder module that will raise the original error.

        Args:
            error: The original loading error

        Returns:
            A placeholder module that raises the error when accessed
        """
        class ErrorPlaceholderModule:
            def __init__(self, name: str, error: Exception):
                self.__name__ = name
                self.__file__ = None
                self.__package__ = name.rsplit('.', 1)[0] if '.' in name else None
                self._error = error

            def __getattr__(self, name: str) -> Any:
                raise self._error

        return ErrorPlaceholderModule(self.module_name, error)

    @staticmethod
    def create_lazy_loader(module_name: str, loader_func: Callable[[], Any]) -> 'LazyLoader':
        """Create a lazy loader for a module.

        Args:
            module_name: The name of the module to load lazily
            loader_func: Function that loads the actual module

        Returns:
            A lazy loader instance
        """
        return LazyLoader(module_name, loader_func)

    @staticmethod
    def is_lazy_loader(obj: Any) -> bool:
        """Check if an object is a lazy loader.

        Args:
            obj: The object to check

        Returns:
            True if the object is a lazy loader
        """
        return isinstance(obj, LazyLoader) or (
            callable(obj) and
            hasattr(obj, '__NAME__') and
            obj.__NAME__ == "__LAZY_MODULE_LOADER__"
        )

    @staticmethod
    def resolve_lazy_loader(obj: Any) -> Any:
        """Resolve a lazy loader to its actual module.

        Args:
            obj: The object to resolve (may be a lazy loader)

        Returns:
            The resolved module or the original object if not a lazy loader
        """
        if LazyLoader.is_lazy_loader(obj):
            if isinstance(obj, LazyLoader):
                return obj()
            else:
                # Legacy lazy loader function
                return obj()
        return obj

