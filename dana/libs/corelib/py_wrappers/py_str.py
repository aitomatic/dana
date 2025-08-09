"""
String conversion function for Dana standard library.

This module provides the str function for converting values to strings.
"""

__all__ = ["py_str"]

from dana.core.lang.sandbox_context import SandboxContext


def py_str(
    context: SandboxContext,
    value: any,
) -> str:
    """Convert a value to a string.

    Args:
        context: The execution context
        value: The value to convert to string

    Returns:
        String representation of the value

    Examples:
        str(123) -> "123"
        str(true) -> "true"
        str([1, 2, 3]) -> "[1, 2, 3]"
    """
    return str(value)
