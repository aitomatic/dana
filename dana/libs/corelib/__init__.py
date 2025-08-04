"""
Dana Core Library

Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Core library functions for the Dana language.

This package provides implementations of core Dana functions including:
- Math functions (sum_range, is_odd, is_even, factorial)
- Basic utility functions
- Core language constructs
"""

# Main registration function
from .register_corelib_functions import register_corelib_functions

__all__ = ["register_corelib_functions"]
