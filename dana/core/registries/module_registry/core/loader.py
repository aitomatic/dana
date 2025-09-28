"""
Module loading and execution.

Handles the actual loading and execution of modules with proper
lifecycle management and error handling.
"""

from typing import Any, Optional, Dict, Tuple
from pathlib import Path
import sys
import importlib.util


class ModuleLoader:
    """Loads and executes modules with proper lifecycle management."""

    def __init__(self):
        """Initialize the module loader."""
        self._loaded_modules: Dict[str, Any] = {}
        self._loading_modules: set = set()
        self._module_cache: Dict[str, Any] = {}

    def load_module(self, module_name: str, file_path: Path, module_type: str) -> Any:
        """Load a module from a file path.

        Args:
            module_name: The name of the module to load
            file_path: The path to the module file
            module_type: The type of module ('dana', 'python', 'namespace')

        Returns:
            The loaded module
        """
        if module_name in self._loaded_modules:
            return self._loaded_modules[module_name]

        if module_name in self._loading_modules:
            # Circular import detected, return a placeholder
            return self._create_placeholder_module(module_name)

        self._loading_modules.add(module_name)

        try:
            if module_type == 'dana':
                module = self._load_dana_module(module_name, file_path)
            elif module_type == 'python':
                module = self._load_python_module(module_name, file_path)
            elif module_type == 'namespace':
                module = self._load_namespace_module(module_name, file_path)
            else:
                raise ImportError(f"Unknown module type: {module_type}")

            self._loaded_modules[module_name] = module
            return module

        finally:
            self._loading_modules.discard(module_name)

    def _load_dana_module(self, module_name: str, file_path: Path) -> Any:
        """Load a Dana module.

        Args:
            module_name: The module name
            file_path: The path to the .na file

        Returns:
            The loaded Dana module
        """
        # Create a basic module object for Dana
        class DanaModule:
            def __init__(self, name: str, file_path: Path):
                self.__name__ = name
                self.__file__ = str(file_path)
                self.__package__ = name.rsplit('.', 1)[0] if '.' in name else None
                self.__dict__ = {}

                # Simulate loading Dana module content
                self._load_content(file_path)

            def _load_content(self, file_path: Path):
                """Load content from Dana file."""
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()

                    # Simple content parsing - look for variable assignments
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            # Simple variable assignment
                            if ' = ' in line:
                                var_name, var_value = line.split(' = ', 1)
                                var_name = var_name.strip()
                                var_value = var_value.strip().strip("'\"")
                                setattr(self, var_name, var_value)
                except Exception as e:
                    print(f"Warning: Could not load Dana module content: {e}")

        return DanaModule(module_name, file_path)

    def _load_python_module(self, module_name: str, file_path: Path) -> Any:
        """Load a Python module.

        Args:
            module_name: The module name
            file_path: The path to the .py file

        Returns:
            The loaded Python module
        """
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _load_namespace_module(self, module_name: str, file_path: Path) -> Any:
        """Load a namespace module (package without __init__).

        Args:
            module_name: The module name
            file_path: The path to the package directory

        Returns:
            The loaded namespace module
        """
        # Create a namespace module object
        class NamespaceModule:
            def __init__(self, name: str, path: Path):
                self.__name__ = name
                self.__file__ = str(path)
                self.__package__ = name
                self.__path__ = [str(path)]
                self.__dict__ = {}

        return NamespaceModule(module_name, file_path)

    def _create_placeholder_module(self, module_name: str) -> Any:
        """Create a placeholder module for circular import situations.

        Args:
            module_name: The name of the module

        Returns:
            A placeholder module
        """
        class PlaceholderModule:
            def __init__(self, name: str):
                self.__name__ = name
                self.__file__ = None
                self.__package__ = name.rsplit('.', 1)[0] if '.' in name else None
                self.__dict__ = {}

            def __getattr__(self, name: str) -> Any:
                # This will be resolved when the actual module is loaded
                raise AttributeError(f"module '{self.__name__}' has no attribute '{name}' (circular import)")

        return PlaceholderModule(module_name)

    def is_loaded(self, module_name: str) -> bool:
        """Check if a module is already loaded.

        Args:
            module_name: The module name to check

        Returns:
            True if the module is loaded
        """
        return module_name in self._loaded_modules

    def get_loaded_module(self, module_name: str) -> Optional[Any]:
        """Get a loaded module.

        Args:
            module_name: The module name

        Returns:
            The loaded module or None if not loaded
        """
        return self._loaded_modules.get(module_name)

    def is_loading(self, module_name: str) -> bool:
        """Check if a module is currently loading.

        Args:
            module_name: The module name to check

        Returns:
            True if the module is currently loading
        """
        return module_name in self._loading_modules

    def unload_module(self, module_name: str) -> None:
        """Unload a module from memory.

        Args:
            module_name: The module name to unload
        """
        self._loaded_modules.pop(module_name, None)
