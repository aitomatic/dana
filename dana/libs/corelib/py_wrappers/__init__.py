"""
Core library Python functions for Dana.

This directory contains all core library Python function files that are preloaded at startup
and automatically available in all Dana programs.
"""

from pathlib import Path

from dana.core.lang.interpreter.functions.function_registry import PreloadedFunctionRegistry

from .register_py_wrappers import _register_python_functions

with PreloadedFunctionRegistry() as registry:
    py_dir = Path(__file__).parent
    _register_python_functions(py_dir, registry)
