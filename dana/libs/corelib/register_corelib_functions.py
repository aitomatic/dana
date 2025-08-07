"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Core library function registration for the Dana interpreter.

This module provides a helper function to automatically register all core library functions in the Dana interpreter.
It supports both Python functions (from py/ directory) and Dana functions (from na/ directory).

The Dana function registration uses Dana's standard module loading system for consistency and maintainability.
"""

import importlib
from pathlib import Path

from dana.common.runtime_scopes import RuntimeScopes
from dana.core.lang.interpreter.executor.function_resolver import FunctionType
from dana.core.lang.interpreter.functions.function_registry import FunctionRegistry


def register_corelib_functions(registry: FunctionRegistry) -> None:
    """Register all core library functions in the function registry.

    This function registers both Python functions (from py/ modules) and Dana functions
    (from na/ modules) in the function registry for use in Dana programs.

    Args:
        registry: The function registry to register functions with
    """
    # Get the corelib directory
    corelib_dir = Path(__file__).parent

    # Register Python functions (from py/ directory)
    py_dir = corelib_dir / "py"
    if py_dir.exists():
        _registered_python_functions = _register_python_functions(py_dir, registry)

    # Register Dana functions (from na/ directory)
    _registered_dana_functions = _register_dana_modules_via_import_system(registry)

    # Register pythonic built-in functions
    from dana.libs.stdlib.pythonic.function_factory import PythonicFunctionFactory, register_pythonic_builtins

    register_pythonic_builtins(registry)
    _pythonic_builtin_functions = list(PythonicFunctionFactory.FUNCTION_CONFIGS.keys())


def _register_python_functions(py_dir: Path, registry: FunctionRegistry) -> list[str]:
    """Register Python functions from .py files in the py/ subdirectory.

    Args:
        py_dir: Path to the py/ subdirectory
        registry: The function registry to register functions with

    Returns:
        List of registered function names
    """
    registered_functions = []

    if not py_dir.exists():
        return registered_functions

    # Find all Python files in the py subdirectory (including py_ prefixed files)
    # Exclude register_core_functions.py as it's for stdlib, not corelib
    python_files = [f for f in py_dir.glob("*.py") if f.is_file() and f.name != "__init__.py" and f.name != "register_core_functions.py"]

    # Import each module and register functions
    for py_file in python_files:
        module_name = f"dana.libs.corelib.py.{py_file.stem}"
        registered_functions.extend(_register_python_module(module_name, registry))

    return registered_functions


def _register_python_module(module_name: str, registry: FunctionRegistry) -> list[str]:
    """Register functions from a Python module.

    Args:
        module_name: Name of the Python module to register
        registry: The function registry to register functions with

    Returns:
        List of registered function names
    """
    registered_functions = []
    try:
        # Import the module
        module = importlib.import_module(module_name)

        # Use __all__ convention to register functions
        if hasattr(module, "__all__"):
            for name in module.__all__:
                if hasattr(module, name):
                    func = getattr(module, name)
                    if callable(func):
                        # Remove 'py_' prefix for Dana registration if present
                        dana_func_name = name[3:] if name.startswith("py_") else name

                        # Register in registry (trusted by default for core library functions)
                        registry.register(
                            name=dana_func_name,
                            func=func,
                            namespace=RuntimeScopes.SYSTEM,
                            func_type=FunctionType.REGISTRY,
                            overwrite=True,
                            trusted_for_context=True,  # Core library functions are always trusted
                        )
                        registered_functions.append(dana_func_name)

    except Exception as e:
        print(f"Corelib: Error registering module {module_name}: {e}")

    return registered_functions


def _register_dana_modules_via_import_system(registry: FunctionRegistry) -> list[str]:
    """Register Dana functions using the standard Dana module system.

    This leverages Dana's module loader to execute modules and discover their contents,
    then registers the discovered functions directly from the loaded module.

    Args:
        registry: The function registry to register functions with

    Returns:
        List of registered function names
    """
    registered_functions = []

    try:
        # Initialize the module system if not already done
        from dana.core.runtime.modules.core import get_module_loader, initialize_module_system

        # Get the corelib na directory and set up search paths
        corelib_dir = Path(__file__).parent
        na_dir = corelib_dir / "na"

        if not na_dir.exists():
            return registered_functions

        # Initialize module system with corelib na directory in search paths
        search_paths = [str(na_dir)]
        initialize_module_system(search_paths)

        # Get the module loader
        loader = get_module_loader()

        # Find all .na modules in the na directory
        na_files = [f for f in na_dir.glob("*.na") if f.name != "__init__.na"]

        for na_file in na_files:
            module_name = na_file.stem

            # Create a module spec
            spec = loader.find_spec(module_name)
            if spec is None:
                print(f"Corelib: Could not find module spec for '{module_name}'")
                continue

            # Create and execute the module
            module = loader.create_module(spec)
            if module is None:
                print(f"Corelib: Could not create module for '{module_name}'")
                continue

            # Execute the module - this discovers and loads all its contents
            loader.exec_module(module)

            # Use the module's __exports__ to determine what to register globally
            if hasattr(module, "__exports__"):
                exports_to_register = module.__exports__
            else:
                # Fallback: register all public attributes
                exports_to_register = {name for name in dir(module) if not name.startswith("_")}

            # Register each exported item
            for export_name in exports_to_register:
                if hasattr(module, export_name):
                    exported_obj = getattr(module, export_name)

                    # Register the object directly (preserves its original type and behavior)
                    registry.register(
                        name=export_name,
                        func=exported_obj,
                        namespace=RuntimeScopes.SYSTEM,
                        func_type=FunctionType.PYTHON,
                        overwrite=True,
                        trusted_for_context=True,
                    )

                    registered_functions.append(export_name)
                    obj_type = type(exported_obj).__name__
                    print(f"Corelib: Registered '{export_name}' ({obj_type}) from {module_name}")

            print(f"Corelib: Module '{module_name}' loaded, {len(exports_to_register)} exports registered")

    except Exception as e:
        print(f"Corelib: Error in Dana module registration: {e}")
        import traceback

        traceback.print_exc()

    return registered_functions


# Dana function wrapper removed - functions now use natural import system instead
