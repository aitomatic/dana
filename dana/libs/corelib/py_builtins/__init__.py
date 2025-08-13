"""
Pythonic built-in functions for Dana.

This module provides Pythonic built-in functions (like len, sum, max, min, etc.)
for the Dana language using a central dispatch approach.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.core.lang.interpreter.functions.function_registry import PreloadedFunctionRegistry

from .register_py_builtins import do_register_py_builtins as _do_register_py_builtins

with PreloadedFunctionRegistry() as registry:
    _do_register_py_builtins(registry)
