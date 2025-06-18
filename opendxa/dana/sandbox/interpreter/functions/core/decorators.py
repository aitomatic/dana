"""
Core decorators for Dana functions.

This module provides decorators that can be used with Dana functions.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any


def log_calls(func: Callable) -> Callable:
    """Decorator that logs function calls and their results.

    Args:
        func: The function to decorate

    Returns:
        The decorated function
    """

    # Get function name, handling DanaFunction objects
    func_name = getattr(func, "__name__", getattr(func, "name", "<unknown>"))

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"[log_calls] Wrapper called for {func_name}")
        print(f"Calling {func_name} with args: {args}, kwargs: {kwargs}")

        # Call the function
        result = func(*args, **kwargs)

        # Log the result
        print(f"{func_name} returned: {result}")

        return result

    return wrapper
