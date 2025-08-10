"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Core library function registration for the Dana interpreter.

This module provides a helper function to automatically register all core library functions in the Dana interpreter.
It supports both Python functions (from py/ directory) and Dana functions (from na/ directory).

The Dana function registration uses Dana's standard module loading system for consistency and maintainability.
"""

from pathlib import Path

from dana.common import DANA_LOGGER
from dana.common.runtime_scopes import RuntimeScopes
from dana.core.lang.interpreter.executor.function_resolver import FunctionType
from dana.core.lang.interpreter.functions.function_registry import FunctionRegistry


def _import_na_modules(registry: FunctionRegistry) -> list[str]:
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

    na_dir = Path(__file__).parent
    if na_dir.exists():
        for na_file in na_dir.rglob("*.na"):
            na_file = na_file.stem
            if na_file == "__init__":
                continue
            # Compute the module import path relative to na_dir's parent
            # rel_path = na_file.relative_to(na_dir.parent)
            # module_parts = rel_path.with_suffix("").parts
            # module_import_path = ".".join(module_parts)
            try:
                from dana.core.runtime.modules.core import get_module_loader, initialize_module_system

                # Ensure the module system is initialized with the correct search path
                search_paths = [str(na_dir)]
                initialize_module_system(search_paths)
                loader = get_module_loader()

                # Import the module using the Dana module loader
                # module_name = module_import_path.replace(".", "/")
                module_name = na_file
                spec = loader.find_spec(module_name)
                if spec is not None:
                    module = loader.create_module(spec)
                    if module is not None:
                        loader.exec_module(module)
            except Exception:
                pass

    return registered_functions


def _import_na_modules_2(registry: FunctionRegistry) -> list[str]:
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
        na_dir = Path(__file__).parent

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
