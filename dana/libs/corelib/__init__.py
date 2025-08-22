"""Initialization library for Dana.

This module provides initialization and startup functionality for Dana applications,
including environment loading, configuration setup, and bootstrap utilities.
"""

# Load core functions into the global registry
# Load Python built-in functions
from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins
from dana.registry import FUNCTION_REGISTRY

do_register_py_builtins(FUNCTION_REGISTRY)

# Load Python wrapper functions
from dana.libs.corelib.py_wrappers.register_py_wrappers import register_py_wrappers

register_py_wrappers(FUNCTION_REGISTRY)

__all__ = []
