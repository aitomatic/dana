"""
Type System for Python-to-Dana Integration

Defines the type mappings and conversion protocols between Python and Dana types.
"""

from enum import Enum
from typing import Any, Protocol


class DanaType(Enum):
    """Dana's built-in types."""

    INT = "int"
    FLOAT = "float"
    STRING = "string"  # Note: Python's str maps to Dana's string
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"
    TUPLE = "tuple"
    SET = "set"
    NULL = "null"  # Note: Python's None maps to Dana's null
    ANY = "any"


class TypeConverter(Protocol):
    """Protocol for type conversion between Python and Dana."""

    def to_dana(self, value: Any) -> tuple[DanaType, Any]:
        """Convert Python value to Dana type."""
        ...

    def from_dana(self, dana_type: DanaType, value: Any) -> Any:
        """Convert Dana value to Python type."""
        ...


# Core type mappings
PYTHON_TO_DANA_TYPES = {
    str: DanaType.STRING,
    int: DanaType.INT,
    float: DanaType.FLOAT,
    bool: DanaType.BOOL,
    list: DanaType.LIST,
    dict: DanaType.DICT,
    tuple: DanaType.TUPLE,
    set: DanaType.SET,
    type(None): DanaType.NULL,
}

# Reverse mapping for Dana to Python
DANA_TO_PYTHON_TYPES = {v: k for k, v in PYTHON_TO_DANA_TYPES.items()}


def get_dana_type(python_value: Any) -> DanaType:
    """Get the corresponding Dana type for a Python value."""
    python_type = type(python_value)
    return PYTHON_TO_DANA_TYPES.get(python_type, DanaType.ANY)


def validate_python_type(value: Any, expected_type: type) -> bool:
    """Validate that a Python value matches the expected type."""
    return isinstance(value, expected_type)


def format_type_error(value: Any, expected_type: type, context: str = "") -> str:
    """Format a clear type error message."""
    actual_type = type(value).__name__
    expected_name = expected_type.__name__

    if context:
        return f"Expected {expected_name}, got {actual_type} at {context}"
    else:
        return f"Expected {expected_name}, got {actual_type}"
