"""
Type Conversion Utilities for Python-to-Dana Integration

Handles conversion between Python and Dana types, including validation
and error reporting.
"""

from typing import Any

from dana.integrations.python.to_dana.core.exceptions import TypeConversionError
from dana.integrations.python.to_dana.core.types import (
    DanaType,
    format_type_error,
    get_dana_type,
    validate_python_type,
)


class BasicTypeConverter:
    """Basic implementation of TypeConverter for common Python types."""

    def to_dana(self, value: Any) -> tuple[DanaType, Any]:
        """Convert Python value to Dana type."""
        try:
            dana_type = get_dana_type(value)

            # For most basic types, the value can be used as-is
            if dana_type in [DanaType.STRING, DanaType.INT, DanaType.FLOAT, DanaType.BOOL, DanaType.NULL]:
                return dana_type, value

            # Handle collections
            elif dana_type == DanaType.LIST:
                # Recursively convert list elements
                converted_items = [self.to_dana(item)[1] for item in value]
                return dana_type, converted_items

            elif dana_type == DanaType.DICT:
                # Recursively convert dictionary values
                converted_dict = {}
                for k, v in value.items():
                    if not isinstance(k, str):
                        raise TypeConversionError(f"Dictionary keys must be strings, got {type(k).__name__}")
                    converted_dict[k] = self.to_dana(v)[1]
                return dana_type, converted_dict

            elif dana_type == DanaType.TUPLE:
                # Convert tuple to list for Dana (Dana doesn't have native tuples)
                converted_items = [self.to_dana(item)[1] for item in value]
                return DanaType.LIST, converted_items

            elif dana_type == DanaType.SET:
                # Convert set to list for Dana (Dana doesn't have native sets)
                converted_items = [self.to_dana(item)[1] for item in list(value)]
                return DanaType.LIST, converted_items

            else:
                # For complex types, try to serialize to dict
                return self._convert_complex_type(value)

        except Exception as e:
            if isinstance(e, TypeConversionError):
                raise
            raise TypeConversionError(f"Failed to convert Python type {type(value).__name__} to Dana: {e}", python_type=type(value))

    def from_dana(self, dana_type: DanaType, value: Any) -> Any:
        """Convert Dana value to Python type."""
        try:
            # Most basic types can be returned as-is
            if dana_type in [DanaType.STRING, DanaType.INT, DanaType.FLOAT, DanaType.BOOL]:
                return value

            elif dana_type == DanaType.NULL:
                return None

            elif dana_type in [DanaType.LIST, DanaType.TUPLE, DanaType.SET]:
                # Recursively convert list elements
                if not isinstance(value, list):
                    raise TypeConversionError(f"Expected list for Dana {dana_type.value}, got {type(value).__name__}")
                return [self.from_dana(get_dana_type(item), item) for item in value]

            elif dana_type == DanaType.DICT:
                # Recursively convert dictionary values
                if not isinstance(value, dict):
                    raise TypeConversionError(f"Expected dict for Dana dict, got {type(value).__name__}")
                converted_dict = {}
                for k, v in value.items():
                    converted_dict[k] = self.from_dana(get_dana_type(v), v)
                return converted_dict

            else:
                # For unknown types, return as-is
                return value

        except Exception as e:
            if isinstance(e, TypeConversionError):
                raise
            raise TypeConversionError(f"Failed to convert Dana type {dana_type.value} to Python: {e}", dana_type=dana_type.value)

    def _convert_complex_type(self, value: Any) -> tuple[DanaType, Any]:
        """Handle conversion of complex Python types."""
        # Try to serialize as JSON-compatible dict
        try:
            if hasattr(value, "__dict__"):
                return DanaType.DICT, {"_type": "object", "class": value.__class__.__name__, "data": value.__dict__}
        except Exception:
            pass

        # Last resort: convert to string representation
        return DanaType.STRING, str(value)


def validate_and_convert(value: Any, expected_type: type, context: str = "") -> Any:
    """Validate a value and provide clear error message if type is wrong."""
    if not validate_python_type(value, expected_type):
        raise TypeError(format_type_error(value, expected_type, context))
    return value
