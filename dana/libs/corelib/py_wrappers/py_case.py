"""
Case function for conditional logic in Dana pipelines.

This module provides the case() function that enables pattern matching
and conditional execution within Dana pipelines, with support for
placeholder expressions ($$).
"""

__all__ = ["py_case"]

from collections.abc import Callable
from typing import Any

from dana.core.lang.sandbox_context import SandboxContext


def py_case(context: SandboxContext, *conditions_and_functions) -> Any:
    """
    Conditional function selection for pipelines.

    Supports multiple patterns:
    1. Explicit condition-function pairs with fallback:
       case((condition1, function1), (condition2, function2), fallback_function)

    2. Placeholder-based conditions:
       case(($$ == value, function), ($$ > threshold, function2), default_function)

    3. Mixed conditions:
       case((external_condition, handler), (True, fallback))

    Args:
        context: Dana execution context
        *conditions_and_functions: Variable arguments of:
            - Tuple pairs: (condition, function) where condition is evaluated
            - Single functions: Used as fallback when no conditions match

    Returns:
        Result of the first matching condition's function, or fallback result

    Raises:
        ValueError: If no condition matches and no fallback provided
        TypeError: If arguments don't match expected patterns

    Examples:
        # Basic usage
        result = input | case(
            ($$ == "json", parse_json),
            ($$ == "xml", parse_xml),
            parse_default
        )

        # With external conditions
        result = data | case(
            (is_development(), debug_handler),
            (is_production(), prod_handler),
            default_handler
        )

        # Multiple conditions on placeholder
        result = value | case(
            ($$ < 0, handle_negative),
            ($$ > 100, handle_large),
            ($$ == 0, handle_zero),
            handle_normal
        )
    """
    if not conditions_and_functions:
        raise ValueError("case() requires at least one argument")

    # Process each argument
    for i, arg in enumerate(conditions_and_functions):
        # Check if this is a condition-function pair (tuple with 2 elements)
        if isinstance(arg, tuple) and len(arg) == 2:
            condition, function = arg

            # Evaluate the condition
            try:
                # The condition could be:
                # 1. A boolean value (already evaluated)
                # 2. A callable that needs to be executed
                # 3. An expression result from placeholder evaluation
                if callable(condition):
                    condition_result = condition(context) if _function_takes_context(condition) else condition()
                else:
                    condition_result = condition

                # If condition is True, execute the associated function
                if condition_result:
                    return _execute_case_function(context, function)

            except Exception:
                # If condition evaluation fails, continue to next condition
                # This allows for graceful handling of placeholder expressions
                # that might fail in certain contexts
                continue

        elif i == len(conditions_and_functions) - 1:
            # Last argument and not a tuple - treat as fallback function
            return _execute_case_function(context, arg)

        else:
            # Middle argument that's not a tuple - this is an error
            raise TypeError(f"Argument {i + 1} must be a (condition, function) tuple, not {type(arg).__name__}")

    # No conditions matched and no fallback provided
    raise ValueError("No conditions matched in case() and no fallback function provided")


def _execute_case_function(context: SandboxContext, function: Any) -> Any:
    """
    Execute a function selected by case(), handling various function types.

    Args:
        context: Dana execution context
        function: Function to execute (can be callable, Dana function, etc.)

    Returns:
        Result of function execution
    """
    if callable(function):
        # Check if function expects a context parameter
        if _function_takes_context(function):
            return function(context)
        else:
            return function()
    else:
        # If it's not callable, return as-is (could be a literal value)
        return function


def _function_takes_context(func: Callable) -> bool:
    """
    Check if a function expects a SandboxContext as its first parameter.

    This is used to determine how to call functions that may or may not
    expect a Dana context parameter.

    Args:
        func: Function to inspect

    Returns:
        True if function appears to take a context parameter
    """
    if not callable(func):
        return False

    try:
        import inspect

        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        # Check if first parameter looks like a context parameter
        if params and len(params) > 0:
            first_param = params[0]
            # Check parameter name or type annotation
            if first_param.name.lower() in ("context", "ctx", "sandbox_context") or (
                hasattr(first_param.annotation, "__name__") and "context" in first_param.annotation.__name__.lower()
            ):
                return True

        return False

    except (ValueError, TypeError, AttributeError):
        # If inspection fails, assume it doesn't take context
        return False
