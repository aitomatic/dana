"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Core library function registration for the Dana interpreter.

This module provides a helper function to automatically register all core library functions in the Dana interpreter.
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
    na_dir = corelib_dir / "na"
    if na_dir.exists():
        # First, load the __init__.na to import all modules
        init_file = na_dir / "__init__.na"
        if init_file.exists():
            _load_init_module(init_file, registry)

        # Then register individual functions as wrappers
        _registered_dana_functions = _register_dana_functions_from_init(registry)

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


def _load_init_module(init_file: Path, registry: FunctionRegistry) -> None:
    """Load the __init__.na module to import all core modules.

    Args:
        init_file: Path to the __init__.na file
        registry: The function registry
    """
    # Ensure the module system is initialized with the correct search paths
    from dana.core.runtime.modules.core import initialize_module_system

    # Get the corelib directory and add it to search paths
    corelib_dir = str(init_file.parent)
    search_paths = [corelib_dir]

    # Initialize the module system with our search paths
    initialize_module_system(search_paths)

    # Execute the __init__.na file to import all modules
    from dana.core.lang.interpreter.dana_interpreter import DanaInterpreter
    from dana.core.lang.sandbox_context import SandboxContext

    interpreter = DanaInterpreter()
    context = SandboxContext()

    with open(init_file, encoding="utf-8") as f:
        init_content = f.read()

    interpreter._eval(init_content, context)

    # Store the context for later use in function wrappers
    registry._init_context = context


def _register_dana_functions_from_init(registry: FunctionRegistry) -> list[str]:
    """Register Dana functions as wrappers to already-imported symbols.

    Args:
        registry: The function registry

    Returns:
        List of registered function names
    """
    registered_functions = []

    # Get the context from the loaded __init__.na
    context = getattr(registry, "_init_context", None)
    if not context:
        return registered_functions

    # Define the functions we want to register from each module
    module_functions = {
        "core": ["add_one", "add_two", "add_three", "add_four"],
        # 'na_agent': ['Agent'],  # No longer needed - BasicAgent is imported directly
    }

    for module_name, func_names in module_functions.items():
        # Get the module object from the context
        if module_name not in context.get_scope("local"):
            continue

        module_obj = context.get_scope("local")[module_name]

        for func_name in func_names:
            if not hasattr(module_obj, func_name):
                continue

            # Create a simple wrapper that calls the imported function
            def create_wrapper(module_obj, func_name):
                def wrapper(*args, **kwargs):
                    # Filter out registry-specific parameters that might conflict
                    filtered_kwargs = {
                        k: v for k, v in kwargs.items() if k not in ["name", "context", "namespace", "func_type", "metadata"]
                    }

                    func = getattr(module_obj, func_name)
                    from dana.core.lang.interpreter.functions.dana_function import DanaFunction

                    if isinstance(func, DanaFunction):
                        # Create a context for the function call
                        from dana.core.lang.sandbox_context import SandboxContext

                        call_context = SandboxContext()
                        return func.execute(call_context, *args, **filtered_kwargs)
                    else:
                        return func(*args, **filtered_kwargs)

                return wrapper

            wrapper_func = create_wrapper(module_obj, func_name)

            # Wrap in PythonFunction for PYTHON type
            from dana.core.lang.interpreter.functions.python_function import PythonFunction

            python_func = PythonFunction(wrapper_func, trusted_for_context=True)

            # Register the wrapper
            registry.register(
                name=func_name,
                func=python_func,
                namespace=RuntimeScopes.SYSTEM,
                func_type=FunctionType.PYTHON,
                overwrite=True,
                trusted_for_context=True,
            )

            registered_functions.append(func_name)

    return registered_functions
