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

from dana.core.runtime.modules.core import initialize_module_system
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
            return ModuleSpec(fullname, self, origin=str(module_file))

        return None

    def create_module(self, spec: ModuleSpec) -> types.ModuleType:
        """Create a new module object."""
        module = types.ModuleType(spec.name)
        module.__file__ = spec.origin
        module.__loader__ = self
        module.__package__ = spec.parent or ""
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

        for search_path in self.search_paths:
            # Try direct .na file
            na_file = search_path / f"{module_name}.na"
            if na_file.exists():
                return na_file

            # Try package with __init__.na
            package_init = search_path / module_name / "__init__.na"
            if package_init.exists():
                return package_init

        return None

    def _is_standard_library_module(self, fullname: str) -> bool:
        """Check if this is a standard library module that should be skipped."""
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
        }

        base_module = fullname.split(".")[0]
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

    if _module_loader and _module_loader in sys.meta_path:
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
