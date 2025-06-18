"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Core function registration for the Dana interpreter.

This module provides a helper function to automatically register all core functions in the Dana interpreter.
"""

import importlib
import inspect
from pathlib import Path

from opendxa.dana.sandbox.interpreter.functions.core.decorators import log_calls, log_with_prefix, repeat, validate_args
from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry


def register_core_functions(registry: FunctionRegistry) -> None:
    """Register all core functions from the core directory.

    This function scans the core/ directory for Python modules and registers
    any function ending with '_function' as a Dana function in the registry.

    Registration order ensures correct function lookup precedence:
    1. Core functions (registered first - highest priority after user functions)
    2. Built-in functions (registered last - lowest priority)

    Args:
        registry: The function registry to register functions with

    Security:
        Core functions have special security status.
    """
    # Get the directory containing this file
    core_dir = Path(__file__).parent

    # Find all Python files in the core directory
    python_files = [f for f in core_dir.glob("*.py") if f.is_file() and f.name != "__init__.py" and f.name != Path(__file__).name]

    # Import each module and register any functions ending with '_function'
    for py_file in python_files:
        module_name = f"opendxa.dana.sandbox.interpreter.functions.core.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)

            # Find all functions in the module
            all_functions = inspect.getmembers(module, inspect.isfunction)
            all_members = inspect.getmembers(module)  # noqa: F841

            for name, obj in all_functions:
                # Register functions ending with '_function'
                if name.endswith("_function"):
                    # Remove '_function' suffix for the registry name
                    dana_func_name = name.replace("_function", "")

                    # Register in registry (trusted by default for core functions)
                    registry.register(
                        name=dana_func_name,
                        func=obj,
                        func_type="dana",
                        overwrite=True,
                        trusted_for_context=True,  # Core functions are always trusted
                    )

        except ImportError:
            # Log import errors but continue with other modules
            pass

    # Register Pythonic built-in functions AFTER core functions
    # This ensures core functions have higher priority than built-ins
    try:
        from opendxa.dana.sandbox.interpreter.functions.pythonic.function_factory import register_pythonic_builtins

        register_pythonic_builtins(registry)
    except ImportError:
        # Pythonic built-ins not available, continue without them
        pass

    # Register decorators (both simple and parameterized)
    registry.register("log_calls", log_calls, namespace="core", func_type="python", trusted_for_context=True)
    registry.register("log_with_prefix", log_with_prefix, namespace="core", func_type="python", trusted_for_context=True)
    registry.register("repeat", repeat, namespace="core", func_type="python", trusted_for_context=True)
    registry.register("validate_args", validate_args, namespace="core", func_type="python", trusted_for_context=True)

    # Register POET decorator
    try:
        from opendxa.dana.poet.decorator import poet

        registry.register("poet", poet, namespace="core", func_type="python", trusted_for_context=True)
    except ImportError:
        # POET module not available, continue without it
        pass
