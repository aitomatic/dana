"""
Control flow optimization modules for Dana language.

This package contains specialized modules for optimizing control flow execution:
- LoopHandler: Optimized loop processing with caching
- ConditionalHandler: Optimized conditional evaluation
- ExceptionHandler: Optimized try/catch/finally blocks
- ContextManagerHandler: Optimized with statement execution
- ControlFlowUtils: Utility functions for simple control flow statements
- Exceptions: Control flow exception classes

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .conditional_handler import ConditionalHandler
from .context_manager_handler import ContextManagerHandler
from .control_flow_utils import ControlFlowUtils
from .exception_handler import ExceptionHandler
from .exceptions import BreakException, ContinueException, ReturnException
from .loop_handler import LoopHandler

__all__ = [
    "LoopHandler",
    "ConditionalHandler",
    "ExceptionHandler",
    "ContextManagerHandler",
    "ControlFlowUtils",
    "BreakException",
    "ContinueException",
    "ReturnException",
]
