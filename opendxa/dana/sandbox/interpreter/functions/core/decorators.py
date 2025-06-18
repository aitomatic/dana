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


def log_with_prefix(prefix: str = "[LOG]", include_result: bool = True) -> Callable:
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


def repeat(times: int = 1) -> Callable:
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


def validate_args(**validators) -> Callable:
    """Parameterized decorator that validates function arguments.

    Args:
        **validators: Dict of parameter_name -> validation_function or type

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        func_name = getattr(func, "__name__", getattr(func, "name", "<unknown>"))

        # Map string type names to actual Python types
        type_mapping = {
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
        }

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            print(f"[validate_args] Validating arguments for {func_name}")

            # For Dana functions, we need to map positional args to parameter names
            if hasattr(func, "parameters"):
                param_names = func.parameters

                # Map positional args to parameter names
                for i, arg_value in enumerate(args):
                    if i < len(param_names):
                        param_name = param_names[i]
                        if param_name in validators:
                            validator = validators[param_name]

                            # Handle string type names
                            if isinstance(validator, str) and validator in type_mapping:
                                validator = type_mapping[validator]

                            # Check if it's a type (for isinstance)
                            if isinstance(validator, type):
                                # Type check
                                if not isinstance(arg_value, validator):
                                    raise TypeError(
                                        f"Parameter '{param_name}' must be of type {validator.__name__}, got {type(arg_value).__name__}"
                                    )
                            elif callable(validator):
                                # Custom validation function
                                if not validator(arg_value):
                                    raise ValueError(f"Validation failed for parameter '{param_name}' with value {arg_value}")

                # Validate keyword arguments
                for param_name, arg_value in kwargs.items():
                    if param_name in validators:
                        validator = validators[param_name]

                        # Handle string type names
                        if isinstance(validator, str) and validator in type_mapping:
                            validator = type_mapping[validator]

                        # Check if it's a type (for isinstance)
                        if isinstance(validator, type):
                            # Type check
                            if not isinstance(arg_value, validator):
                                raise TypeError(
                                    f"Parameter '{param_name}' must be of type {validator.__name__}, got {type(arg_value).__name__}"
                                )
                        elif callable(validator):
                            # Custom validation function
                            if not validator(arg_value):
                                raise ValueError(f"Validation failed for parameter '{param_name}' with value {arg_value}")

            print(f"[validate_args] All validations passed for {func_name}")
            return func(*args, **kwargs)

        return wrapper

    return decorator
