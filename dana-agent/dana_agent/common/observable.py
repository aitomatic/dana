"""
Observable decorator for tracking function calls with Langfuse.

This module provides an `observable` decorator that automatically tracks
function inputs and outputs using Langfuse for observability and monitoring.

Langfuse tracking can be disabled by setting the LANGFUSE_ENABLED environment
variable to 'false' (default). Set to 'true', '1', or 'yes' to enable tracking.
"""

import functools
import os
from collections.abc import Callable

from langfuse import Langfuse
from langfuse import observe as langfuse_observe

# Check if Langfuse should be enabled
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "false").lower() in ("true", "1", "yes")

if LANGFUSE_ENABLED:
    OBSERVER = Langfuse()
else:
    OBSERVER = None


def observable(*args, **kwargs) -> Callable:
    """
    Decorator that tracks function calls with Langfuse and flushes after execution.

    This decorator applies the @langfuse_observe() decorator with all provided parameters
    and automatically calls OBSERVER.flush() after the function executes. This ensures
    that all observations are sent to Langfuse immediately after function completion.

    Note: Langfuse tracking is disabled by default. Set LANGFUSE_ENABLED=true to enable.

    Args:
        *args: Positional arguments passed to langfuse_observe
        **kwargs: Keyword arguments passed to langfuse_observe (e.g., name, tags, as_type)

    Examples:
        Basic usage:
            @observable()
            def my_function(self, *args, **kwargs):
                return "result"

        With custom span name:
            @observable(name="custom_span_name")
            def my_function():
                return "result"

        With tags and type:
            @observable(name="api_call", tags=["production", "api"], as_type="generation")
            def api_function():
                return "api_response"

        With all langfuse_observe parameters:
            @observable(
                name="complex_operation",
                tags=["ml", "inference"],
                as_type="generation",
                session_id="session_123"
            )
            def ml_function():
                return "prediction"

    Returns:
        Decorated function that automatically tracks inputs and outputs using Langfuse,
        with automatic flushing after execution.
    """

    def decorator(func: Callable) -> Callable:
        # Apply the langfuse_observe decorator with all parameters
        if LANGFUSE_ENABLED:
            execute_function = langfuse_observe(*args, **kwargs)(func)
        else:
            execute_function = func

        @functools.wraps(func)
        def wrapper(*wrapper_args, **wrapper_kwargs):
            # Execute the observed function
            result = execute_function(*wrapper_args, **wrapper_kwargs)
            # Flush after execution
            if OBSERVER:
                OBSERVER.flush()
            return result

        return wrapper

    # Handle both @observable and @observable() syntax
    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        # Called as @observable (without parentheses) - no parameters passed
        func = args[0]
        # Apply langfuse_observe with no parameters
        if LANGFUSE_ENABLED:
            execute_function = langfuse_observe(func)
        else:
            execute_function = func

        @functools.wraps(func)
        def wrapper(*wrapper_args, **wrapper_kwargs):
            # Execute the observed function
            result = execute_function(*wrapper_args, **wrapper_kwargs)
            # Flush after execution
            if OBSERVER:
                OBSERVER.flush()
            return result

        return wrapper
    else:
        # Called as @observable() or @observable(...) (with parentheses/parameters)
        return decorator
