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

from dana.common import DANA_LOGGER
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

    #
    # Register Python functions (from py/ directory) next. They can override the pythonic built-in functions.
    #
    py_dir = corelib_dir / "py"
    if py_dir.exists():
        _registered_python_functions = _register_python_functions(py_dir, registry)

    #
    # Register Dana functions last (from na/ directory), so that they can use or override the Python functions
    #
    _registered_dana_functions = _register_dana_modules_via_import_system(registry)


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
        module_name = f"dana.libs.corelib.py_wrappers.{py_file.stem}"
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

    except Exception:
        # Silently handle registration errors
        pass

    return registered_functions


def _register_dana_modules_via_import_system_2(registry: FunctionRegistry) -> list[str]:
    """Register Dana functions using the standard Dana module system.

    This leverages Dana's module loader to execute modules and discover their contents,
    then registers the discovered functions directly from the loaded module.

    Args:
        registry: The function registry to register functions with

    Returns:
        List of registered function names
    """
    registered_functions = []

    # Scan for all .na files in corelib_dir/na and all its subdirectories, and import them one at a time
    from pathlib import Path

    na_dir = Path(__file__).parent / "na"
    if na_dir.exists():
        for na_file in na_dir.rglob("*.na"):
            if na_file.name == "__init__.na":
                continue
            # Compute the module import path relative to na_dir's parent
            rel_path = na_file.relative_to(na_dir.parent)
            module_parts = rel_path.with_suffix("").parts
            module_import_path = ".".join(module_parts)
            import_stmt = f"from {module_import_path} import WHAT_EVER"
            DANA_LOGGER.error(f"CTN Importing statement: {import_stmt}")
            try:
                from dana.core.runtime.modules.core import get_module_loader, initialize_module_system

                # Ensure the module system is initialized with the correct search path
                search_paths = [str(na_dir)]
                initialize_module_system(search_paths)
                loader = get_module_loader()

                # Import the module using the Dana module loader
                module_name = module_import_path.replace(".", "/")
                spec = loader.find_spec(module_name)
                if spec is not None:
                    module = loader.create_module(spec)
                    if module is not None:
                        loader.exec_module(module)
            except Exception:
                pass

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
            DANA_LOGGER.error(f"CTN Registering Dana module: {na_file}")
            module_name = na_file.stem

            # Create a module spec
            spec = loader.find_spec(module_name)
            if spec is None:
                continue

            # Create and execute the module
            module = loader.create_module(spec)
            if module is None:
                continue

            # Execute the module - this discovers and loads all its contents
            DANA_LOGGER.error(f"CTN Executing module: {module.__name__}")
            loader.exec_module(module)

            # Use the module's __exports__ to determine what to register globally
            if hasattr(module, "__exports__"):
                exports_to_register = module.__exports__
            else:
                # Fallback: register all public attributes
                exports_to_register = {name for name in dir(module) if not name.startswith("_")}

            DANA_LOGGER.error(f"CTN Exports to register: {exports_to_register}")

            # Register each exported item
            for export_name in exports_to_register:
                if hasattr(module, export_name):
                    exported_obj = getattr(module, export_name)

                    DANA_LOGGER.error(f"CTN Registering function: {export_name}")

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

    except Exception as e:
        # Silently handle errors to avoid cluttering output
        DANA_LOGGER.error(f"CTN Error registering Dana module: {e}")
        pass

    return registered_functions


# Dana function wrapper removed - functions now use natural import system instead
