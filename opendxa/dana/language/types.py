"""DANA type system and type checking utilities."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class DanaType(Enum):
    """Core DANA types."""

    INTEGER = "integer"
    STRING = "string"
    BOOLEAN = "boolean"
    LIST = "list"
    NONE = "none"


@dataclass
class TypeInfo:
    """Type information for a value or expression."""

    type: DanaType
    value: Optional[Any] = None


def infer_type(value: Any) -> TypeInfo:
    """Infer the DANA type of a Python value."""
    if isinstance(value, int):
        return TypeInfo(type=DanaType.INTEGER, value=value)
    elif isinstance(value, str):
        return TypeInfo(type=DanaType.STRING, value=value)
    elif isinstance(value, bool):
        return TypeInfo(type=DanaType.BOOLEAN, value=value)
    elif isinstance(value, list):
        return TypeInfo(type=DanaType.LIST, value=value)
    elif value is None:
        return TypeInfo(type=DanaType.NONE)
    else:
        raise ValueError(f"Cannot infer DANA type for value: {value}")


def check_type_compatibility(expected: DanaType, actual: DanaType) -> bool:
    """Check if two types are compatible for assignment or comparison."""
    # For now, we only allow exact type matches
    # This can be extended later for more flexible type compatibility
    return expected == actual


def validate_identifier(name: str) -> bool:
    """Validate an identifier name follows DANA syntax rules.

    Allows multi-part identifiers like scope.subscope.variable.
    """
    if not name:
        return False

    parts = name.split(".")
    if not parts:  # Should not happen if name is not empty, but safe check
        return False

    # Check each part of the identifier
    for part in parts:
        if not part:  # Check for empty parts (e.g., "scope..variable")
            return False
        if not part[0].isalpha() and part[0] != "_":  # Must start with letter or underscore
            return False
        if not all(c.isalnum() or c == "_" for c in part):  # Must contain only letters, numbers, underscores
            return False

    return True
