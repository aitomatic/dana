"""
Copyright © 2025 Aitomatic, Inc.

This source code is licensed under the license found in the LICENSE file in the root directory of this source tree

Functions infrastructure for the Dana interpreter.

This package provides the core infrastructure for function handling:
- Function registry system
- Base function classes
- Function execution framework
"""

# Import infrastructure components only
from dana.registry.function_registry import FunctionRegistry

from .argument_processor import ArgumentProcessor
from .composed_function import ComposedFunction
from .dana_function import DanaFunction

__all__ = ["FunctionRegistry", "DanaFunction", "ArgumentProcessor", "ComposedFunction"]
