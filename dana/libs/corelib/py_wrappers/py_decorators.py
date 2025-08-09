"""
Core decorators for Dana functions.

This module provides decorators that can be used with Dana functions.
"""

__all__ = ["py_log_calls", "py_log_with_prefix", "py_repeat", "py_validate_args"]

from collections.abc import Callable
from functools import wraps
from typing import Any


def py_log_calls(func: Callable) -> Callable:
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


def py_log_with_prefix(prefix: str = "[LOG]", include_result: bool = True) -> Callable:
    """Parameterized decorator that logs function calls with a custom prefix.

    Args:
        prefix: Custom prefix for log messages
        include_result: Whether to log the return value

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        func_name = getattr(func, "__name__", getattr(func, "name", "<unknown>"))

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            print(f"{prefix} Calling {func_name} with args: {args}, kwargs: {kwargs}")

            result = func(*args, **kwargs)

            if include_result:
                print(f"{prefix} {func_name} returned: {result}")

            return result

        return wrapper

    return decorator


def py_repeat(times: int = 1) -> Callable:
    """Parameterized decorator that repeats function execution.

    Args:
        times: Number of times to execute the function

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        func_name = getattr(func, "__name__", getattr(func, "name", "<unknown>"))

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            print(f"[repeat] Executing {func_name} {times} times")

            result = None
            for i in range(times):
                print(f"[repeat] Execution {i + 1}/{times}")
                result = func(*args, **kwargs)

            return result

        return wrapper

    return decorator


def py_validate_args(**validators) -> Callable:
    """Parameterized decorator that validates function arguments.

    Args:
        **validators: Keyword arguments mapping parameter names to validation functions

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        func_name = getattr(func, "__name__", getattr(func, "name", "<unknown>"))

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            print(f"[validate_args] Validating arguments for {func_name}")

            # Validate arguments based on validators
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if not validator(value):
                        raise ValueError(f"Validation failed for {param_name}: {value}")

            result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator
