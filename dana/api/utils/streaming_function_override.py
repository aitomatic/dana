"""
Streaming Function Override Context Manager

This module provides a context manager to temporarily override Dana functions
like print() to enable real-time streaming during execution.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, Optional, Union, Callable, Awaitable
from contextlib import contextmanager

from dana.core.lang.interpreter.functions.function_registry import FunctionRegistry
from dana.core.lang.interpreter.executor.function_resolver import FunctionType
from dana.api.utils.streaming_print_function import streaming_print_function, StreamingPrintManager


@contextmanager
def streaming_print_override(
    registry: FunctionRegistry,
    log_streamer: Optional[Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]]] = None
):
    """
    Context manager to temporarily override the print function with streaming version.
    
    Args:
        registry: The function registry to modify
        log_streamer: Optional callback for streaming log messages
        
    Yields:
        The context manager
    """
    # Store original print function
    original_print = None
    try:
        # Get the original print function if it exists
        original_print = registry.get_function("print")
    except Exception:
        pass  # No existing print function
    
    # Set the log streamer
    if log_streamer:
        StreamingPrintManager.set_streamer(log_streamer)
    
    try:
        # Register our streaming print function
        registry.register(
            name="print",
            func=streaming_print_function,
            func_type=FunctionType.REGISTRY,
            overwrite=True,
            trusted_for_context=True
        )
        
        yield
        
    finally:
        # Restore original print function
        if original_print:
            registry.register(
                name="print", 
                func=original_print.func,
                func_type=original_print.func_type,
                overwrite=True,
                trusted_for_context=True
            )
        
        # Clear the log streamer
        StreamingPrintManager.clear_streamer()