"""
Dana Module Import Hook for Python-to-Dana Integration

Provides the ability to import Dana .na files directly in Python code while
maintaining the same security and architectural patterns as the existing
python_to_dana integration.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import sys
import types
from collections.abc import Sequence
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Any

from dana.__init__ import initialize_module_system
from dana.integrations.python.to_dana.core.exceptions import DanaCallError
from dana.integrations.python.to_dana.core.inprocess_sandbox import InProcessSandboxInterface
from dana.integrations.python.to_dana.core.sandbox_interface import SandboxInterface


class DanaModuleWrapper:
    """Wrapper for imported Dana modules that provides Pythonic access."""

    def __init__(self, module_name: str, sandbox_interface: SandboxInterface, context, debug: bool = False):
        """Initialize the Dana module wrapper.

        Args:
            module_name: Name of the Dana module
            sandbox_interface: Sandbox interface for execution
            context: Dana execution context
            debug: Enable debug mode
        """
        self._module_name = module_name
        self._sandbox_interface = sandbox_interface
        self._context = context
        self._debug = debug
        self._functions = {}
        self._variables = {}

        # Extract functions and variables from context
        self._extract_module_contents()

    def _extract_module_contents(self):
        """Extract functions and variables from the Dana context."""
        try:
            # Get local scope variables
            local_vars = self._context.get_scope("local")
            for name, value in local_vars.items():
                if not name.startswith("_"):
                    if callable(value):
                        self._functions[name] = value
                    else:
                        self._variables[name] = value

            # Get public scope variables
            public_vars = self._context.get_scope("public")
            for name, value in public_vars.items():
                if not name.startswith("_"):
                    self._variables[name] = value

            # Allow to get agent_name, agent_description only in system scope
            system_vars = self._context.get_scope("system")
            for name, value in system_vars.items():
                if name in ["agent_name", "agent_description"]:
                    self._variables[name] = value

        except Exception as e:
            if self._debug:
                print(f"DEBUG: Error extracting module contents: {e}")

    def __getattr__(self, name: str) -> Any:
        """Get attribute from the Dana module."""
        # Check for functions first
        if name in self._functions:
            return self._create_function_wrapper(name, self._functions[name])

        # Check for variables
        if name in self._variables:
            return self._variables[name]

        # Check for special attributes
        if name == "__name__":
            return self._module_name
        elif name == "__dana_context__":
            return self._context
        elif name == "__dana_sandbox__":
            return self._sandbox_interface

        raise AttributeError(f"Dana module '{self._module_name}' has no attribute '{name}'")

    def _create_function_wrapper(self, func_name: str, dana_func: Any) -> callable:
        """Create a Python wrapper for a Dana function."""

        def python_wrapper(*args, **kwargs):
            try:
                if self._debug:
                    print(f"DEBUG: Calling Dana function '{func_name}' with args={args}, kwargs={kwargs}")

                # Execute through sandbox interface using the new execute_function method
                result = self._sandbox_interface.execute_function(func_name, args, kwargs)
                # The result may be an EagerPromise object - this is expected behavior
                # Promise transparency will handle resolution when the result is accessed
                return result

            except Exception as e:
                if isinstance(e, DanaCallError):
                    raise
                raise DanaCallError(f"Error calling Dana function '{func_name}': {e}") from e

        # Copy function metadata
        python_wrapper.__name__ = func_name
        python_wrapper.__doc__ = getattr(dana_func, "__doc__", f"Dana function: {func_name}")
        python_wrapper.__dana_function__ = dana_func

        return python_wrapper

    def __dir__(self) -> list[str]:
        """Return list of available attributes."""
        return list(self._functions.keys()) + list(self._variables.keys()) + ["__name__", "__dana_context__", "__dana_sandbox__"]

    def __repr__(self) -> str:
        """String representation of the Dana module."""
        func_count = len(self._functions)
        var_count = len(self._variables)
        return f"DanaModule('{self._module_name}', {func_count} functions, {var_count} variables)"


class DanaModuleLoader(MetaPathFinder, Loader):
    """Python import hook for loading Dana .na files with python_to_dana integration."""

    def __init__(self, search_paths: list[str] | None = None, sandbox_interface: SandboxInterface | None = None, debug: bool = False):
        """Initialize the Dana module loader.

        Args:
            search_paths: List of paths to search for .na files
            sandbox_interface: Sandbox interface to use for execution
            debug: Enable debug mode
        """
        if search_paths is None:
            search_paths = [
                str(Path.cwd()),
                str(Path.cwd() / "dana"),
            ]

        self.search_paths = [Path(p).resolve() for p in search_paths]
        self._sandbox_interface = sandbox_interface or InProcessSandboxInterface(debug=debug)
        self._debug = debug
        self._loaded_modules = {}

        # Initialize Dana module system
        try:
            initialize_module_system(search_paths)
        except Exception:
            # Already initialized
            pass

        if debug:
            print(f"DEBUG: DanaModuleLoader initialized with {len(self.search_paths)} search paths")

    def find_spec(self, fullname: str, path: Sequence[str] | None = None, target: types.ModuleType | None = None) -> ModuleSpec | None:
        """Find a module specification for Dana modules."""

        # Only handle modules that don't exist in Python already
        if fullname in sys.modules:
            return None

        # Skip standard library and common packages
        if self._is_standard_library_module(fullname):
            return None

        # Look for .na file
        module_file = self._find_dana_module(fullname)
        if module_file:
            if self._debug:
                print(f"DEBUG: Found Dana module '{fullname}' at {module_file}")

            spec = ModuleSpec(fullname, self, origin=str(module_file))

            # Set up package attributes for directory packages
            if module_file.is_dir():
                spec.submodule_search_locations = [str(module_file)]

            return spec

        return None

    def create_module(self, spec: ModuleSpec) -> types.ModuleType:
        """Create a new module object."""
        module = types.ModuleType(spec.name)
        module.__file__ = spec.origin
        module.__loader__ = self

        # Set up package attributes
        origin_path = Path(spec.origin)
        if spec.origin.endswith("__init__.na"):
            # Legacy __init__.na package
            module.__path__ = [str(origin_path.parent)]
            module.__package__ = spec.name
        elif origin_path.is_dir():
            # Directory package (new)
            module.__path__ = [str(origin_path)]
            module.__package__ = spec.name
        elif "." in spec.name:
            # Submodule of a package
            module.__package__ = spec.name.rsplit(".", 1)[0]
        else:
            # Top-level module
            module.__package__ = ""

        return module

    def exec_module(self, module: types.ModuleType) -> None:
        """Execute a Dana module and populate the Python module."""
        if not module.__file__:
            raise ImportError(f"No file specified for module {module.__name__}")

        try:
            # Check if already loaded
            if module.__name__ in self._loaded_modules:
                dana_wrapper = self._loaded_modules[module.__name__]
            else:
                if self._debug:
                    print(f"DEBUG: Executing Dana module '{module.__name__}' from {module.__file__}")

                # Handle directory packages (no code to execute)
                module_path = Path(module.__file__)
                if module_path.is_dir():
                    # Directory package - create empty wrapper
                    from dana.core.lang.sandbox_context import SandboxContext

                    empty_context = SandboxContext()
                    dana_wrapper = DanaModuleWrapper(module.__name__, self._sandbox_interface, empty_context, self._debug)
                else:
                    # Execute the Dana module through sandbox interface using new exec_module method
                    result = self._sandbox_interface.exec_module(module.__file__)
                    if not result.success:
                        raise ImportError(f"Failed to execute Dana module {module.__name__}: {result.error}")

                    # Create wrapper for the module
                    dana_wrapper = DanaModuleWrapper(module.__name__, self._sandbox_interface, result.final_context, self._debug)

                # Cache the loaded module
                self._loaded_modules[module.__name__] = dana_wrapper

            # Transfer attributes from Dana wrapper to Python module
            for attr_name in dir(dana_wrapper):
                if not attr_name.startswith("_") or attr_name in ["__name__", "__dana_context__", "__dana_sandbox__"]:
                    setattr(module, attr_name, getattr(dana_wrapper, attr_name))

            # Add the Dana wrapper as a special attribute
            module.__dana_wrapper__ = dana_wrapper

        except Exception as e:
            if isinstance(e, ImportError):
                raise
            raise ImportError(f"Failed to load Dana module {module.__name__}: {e}") from e

    def _find_dana_module(self, fullname: str) -> Path | None:
        """Find a Dana .na file for the given module name."""
        module_name = fullname.split(".")[-1]

        # If this is a submodule (contains dots), check if parent package is already loaded
        if "." in fullname:
            parent_name = fullname.rsplit(".", 1)[0]
            if parent_name in sys.modules:
                parent_module = sys.modules[parent_name]
                if hasattr(parent_module, "__path__"):
                    # Search in parent package's search locations
                    for parent_path in parent_module.__path__:
                        parent_path_obj = Path(parent_path)

                        # Try direct .na file
                        na_file = parent_path_obj / f"{module_name}.na"
                        if na_file.exists():
                            return na_file

                        # Try package with __init__.na (legacy support)
                        package_init = parent_path_obj / module_name / "__init__.na"
                        if package_init.exists():
                            return package_init

                        # Try directory package (new: directories containing .na files are packages)
                        package_dir = parent_path_obj / module_name
                        if package_dir.is_dir() and self._is_dana_package_directory(package_dir):
                            return package_dir

        # Search in configured search paths
        for search_path in self.search_paths:
            # Try direct .na file
            na_file = search_path / f"{module_name}.na"
            if na_file.exists():
                return na_file

            # Try package with __init__.na (legacy support)
            package_init = search_path / module_name / "__init__.na"
            if package_init.exists():
                return package_init

            # Try directory package (new: directories containing .na files are packages)
            package_dir = search_path / module_name
            if package_dir.is_dir() and self._is_dana_package_directory(package_dir):
                return package_dir

        return None

    def _is_dana_package_directory(self, directory: Path) -> bool:
        """Check if a directory qualifies as a Dana package.

        A directory is considered a Dana package if it contains:
        - At least one .na file, OR
        - At least one subdirectory that is also a Dana package

        Args:
            directory: Directory to check

        Returns:
            True if directory is a Dana package, False otherwise
        """
        if not directory.is_dir():
            return False

        # Check for direct .na files
        for item in directory.iterdir():
            if item.is_file() and item.suffix == ".na":
                return True

        # Check for subdirectory packages
        for item in directory.iterdir():
            if item.is_dir():
                # Check if subdirectory has __init__.na (legacy packages)
                if (item / "__init__.na").exists():
                    return True
                # Check if subdirectory is itself a Dana package (recursive)
                if self._is_dana_package_directory(item):
                    return True

        return False

    def _is_standard_library_module(self, fullname: str) -> bool:
        """Check if this is a standard library module that should be skipped."""
        # First check: modules already loaded in sys.modules should be skipped
        # This handles all third-party packages automatically
        base_module = fullname.split(".")[0]
        if base_module in sys.modules:
            return True

        # Second check: known standard library and common third-party modules
        stdlib_modules = {
            "os",
            "sys",
            "json",
            "math",
            "datetime",
            "pathlib",
            "importlib",
            "types",
            "collections",
            "itertools",
            "functools",
            "operator",
            "threading",
            "asyncio",
            "concurrent",
            "multiprocessing",
            "numpy",
            "pandas",
            "matplotlib",
            "requests",
            "flask",
            "django",
            "pytest",
            "unittest",
            "logging",
            "argparse",
            "subprocess",
            "io",
            "tempfile",
            "shutil",
            "glob",
            "re",
            "random",
            "hashlib",
            "dana",
            "llama_index",
            "openai",
            "anthropic",
            "aisuite",
        }

        return base_module in stdlib_modules or base_module.startswith("_")


# Global loader instance
_module_loader: DanaModuleLoader | None = None


def install_import_hook(
    search_paths: list[str] | None = None, sandbox_interface: SandboxInterface | None = None, debug: bool = False
) -> None:
    """Install the Dana module import hook.

    Args:
        search_paths: Optional list of paths to search for .na files
        sandbox_interface: Optional sandbox interface to use
        debug: Enable debug mode
    """
    global _module_loader

    if _module_loader is None:
        _module_loader = DanaModuleLoader(search_paths, sandbox_interface, debug)
        sys.meta_path.insert(0, _module_loader)
        if debug:
            print("Dana module import hook installed!")


def uninstall_import_hook() -> None:
    """Uninstall the Dana module import hook."""
    global _module_loader

    if _module_loader and sys.meta_path and _module_loader in sys.meta_path:
        sys.meta_path.remove(_module_loader)
        _module_loader = None
        print("Dana module import hook uninstalled!")


def list_available_modules(search_paths: list[str] | None = None) -> list[str]:
    """List all available Dana modules.

    Args:
        search_paths: Optional list of paths to search

    Returns:
        List of available module names
    """
    if search_paths is None:
        search_paths = [
            str(Path.cwd()),
            str(Path.cwd() / "dana"),
        ]

    modules = []
    for search_path in search_paths:
        search_path = Path(search_path)
        if search_path.exists():
            # Find .na files
            for na_file in search_path.glob("*.na"):
                if not na_file.name.startswith("_"):
                    modules.append(na_file.stem)

            # Find packages with __init__.na
            for package_dir in search_path.iterdir():
                if package_dir.is_dir():
                    init_file = package_dir / "__init__.na"
                    if init_file.exists():
                        modules.append(package_dir.name)

    return sorted(list(set(modules)))
