"""
Function resolver package for unified function dispatch.

This package provides the new unified function resolution system that replaces
the fragmented function lookup mechanisms across the Dana interpreter.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .base_resolver import FunctionResolverInterface, ResolutionAttempt
from .unified_function_dispatcher import UnifiedFunctionDispatcher

__all__ = [
    "FunctionResolverInterface",
    "ResolutionAttempt",
    "UnifiedFunctionDispatcher",
]
