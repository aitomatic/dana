"""
Type checking function for Dana standard library.

This module provides the isinstance function for type checking.
"""

__all__ = ["py_isinstance"]

from typing import Any, Union

from dana.core.lang.sandbox_context import SandboxContext


def py_isinstance(context: SandboxContext, obj: Any, class_or_tuple: Union[str, tuple[str, ...]]) -> bool:
    """Check if an object is an instance of a class or a subclass thereof.

    This function mimics Python's built-in isinstance() function.
    It checks if the given object's type name matches the specified type name(s).

    Args:
        context: The execution context
        obj: The object to check
        class_or_tuple: A type name string or a tuple of type name strings to check against

    Returns:
        True if obj's type name matches class_or_tuple, False otherwise

    Examples:
        isinstance(5, "int") -> True
        isinstance("hello", "str") -> True
        isinstance(3.14, ("int", "float")) -> True
        isinstance("hello", "int") -> False
        isinstance([1, 2, 3], "list") -> True
        isinstance({"a": 1}, "dict") -> True
    """
    # Get the type name of the object
    obj_type_name = type(obj).__name__

    # Handle single type name
    if isinstance(class_or_tuple, str):
        return obj_type_name == class_or_tuple

    # Handle tuple of type names
    elif isinstance(class_or_tuple, tuple):
        return obj_type_name in class_or_tuple

    # Handle other cases
    else:
        return False
