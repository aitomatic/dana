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
    """Validate an identifier name follows DANA syntax rules."""
    if not name:
        return False

    # Check for valid scope.variable format
    parts = name.split(".")
    if len(parts) != 2:
        return False

    scope, variable = parts

    # Check scope and variable names
    for part in [scope, variable]:
        if not part[0].isalpha() and part[0] != "_":
            return False
        if not all(c.isalnum() or c == "_" for c in part):
            return False

    return True
