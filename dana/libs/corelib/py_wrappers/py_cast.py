"""
Type casting function for Dana standard library.

This module provides the cast function for type conversion.
"""

__all__ = ["py_cast"]

from typing import Any

from dana.core.lang.sandbox_context import SandboxContext


def py_cast(context: SandboxContext, target_type: Any, value: Any) -> Any:
    """Cast a value to a specified type.

    Args:
        context: The execution context
        target_type: The target type to cast to
        value: The value to cast

    Returns:
        The value cast to the target type

    Examples:
        cast(int, "123") -> 123
        cast(str, 456) -> "456"
        cast(float, "3.14") -> 3.14
    """
    if target_type == int:
        return int(value)
    elif target_type == str:
        return str(value)
    elif target_type == float:
        return float(value)
    elif target_type == bool:
        return bool(value)
    else:
        raise TypeError(f"Cannot cast to type {target_type}")
