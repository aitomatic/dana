"""Initialization library for Dana.

This module provides initialization and startup functionality for Dana applications,
including environment loading, configuration setup, and bootstrap utilities.
"""

# Load core functions into the global registry
# Load Python built-in functions
from dana.libs.corelib.py_builtins.register_py_builtins import do_register_py_builtins
from dana.registry import get_global_registry

do_register_py_builtins(get_global_registry().functions)

# Load Python wrapper functions
from dana.libs.corelib.py_wrappers.register_py_wrappers import register_py_wrappers

register_py_wrappers(get_global_registry().functions)

__all__ = []
