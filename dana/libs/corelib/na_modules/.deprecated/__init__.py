"""
Pythonic built-in functions for Dana.

This module provides Pythonic built-in functions (like len, sum, max, min, etc.)
for the Dana language using a central dispatch approach.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

if False:
    from .import_na_modules import _import_na_modules
    from dana.core.lang.interpreter.functions.function_registry import PreloadedFunctionRegistry

    with PreloadedFunctionRegistry() as registry:
        _import_na_modules(registry)
