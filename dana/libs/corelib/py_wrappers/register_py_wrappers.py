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
from dana.registry.function_registry import FunctionRegistry


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
    python_files = [f for f in py_dir.glob("py_*.py")]

    # Import each module and register functions
    import dana.libs.corelib.py_wrappers as py_wrappers_module

    for py_file in python_files:
        module_name = f"{py_wrappers_module.__name__}.{py_file.stem}"
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


def register_py_wrappers(registry: FunctionRegistry) -> list[str]:
    """Register all Python wrapper functions in the function registry.

    Args:
        registry: The function registry to register functions with

    Returns:
        List of registered function names
    """
    registered_functions = []

    # Get the py_wrappers directory
    py_wrappers_dir = Path(__file__).parent

    # Register Python functions from py_* modules
    registered_functions.extend(_register_python_functions(py_wrappers_dir, registry))

    return registered_functions


# Alias for backward compatibility
register_core_functions = register_py_wrappers
