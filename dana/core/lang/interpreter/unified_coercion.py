"""
Unified Type Coercion System

This module provides a unified interface that replaces the old TypeCoercion class
with enhanced semantic coercion capabilities while maintaining backward compatibility.
"""

import os
from typing import Any

from dana.common.mixins.loggable import Loggable
from dana.core.lang.interpreter.enhanced_coercion import CoercionStrategy, SemanticCoercer


class UnifiedTypeCoercion(Loggable):
    """
    Unified type coercion system that replaces TypeCoercion with enhanced capabilities.

    This class provides a drop-in replacement for the old TypeCoercion class while
    using the enhanced semantic coercion engine under the hood.
    """

    def __init__(self):
        super().__init__()
        self.semantic_coercer = SemanticCoercer(strategy=CoercionStrategy.ENHANCED)

    @staticmethod
    def can_coerce(value: Any, target_type: type) -> bool:
        """
        Check if a value can be safely coerced to target type.

        Enhanced version that supports more coercion types than the old system.

        Args:
            value: The value to potentially coerce
            target_type: The target type to coerce to

        Returns:
            True if coercion is safe and recommended
        """
        if isinstance(value, target_type):
            return True

        # Support None values - None can be assigned to any type
        # This allows for optional/nullable types in Dana
        if value is None:
            return True

        # Enhanced: Support float -> int coercion (with truncation warning)
        if target_type is int and isinstance(value, float):
            return True

        # Safe numeric upward conversions
        if target_type is float and isinstance(value, int):
            return True

        # Safe string conversions for display/concatenation
        if target_type is str and isinstance(value, int | float | bool | dict | list):
            return True

        # Enhanced: Support dict and list coercion from JSON strings
        if target_type in (dict, list) and isinstance(value, str):
            return True

        # String to numeric conversions (if parseable)
        if isinstance(value, str) and target_type in (int, float):
            try:
                target_type(value.strip())
                return True
            except (ValueError, TypeError):
                return False

        # Enhanced semantic coercion: string to bool (always possible)
        if target_type is bool and isinstance(value, str):
            return True

        # Enhanced: Support more flexible bool coercion
        if target_type is bool and isinstance(value, int | float):
            return True

        return False

    def coerce_value(self, value: Any, target_type: type) -> Any:
        """
        Coerce a value to target type using enhanced semantic coercion.

        Args:
            value: The value to coerce
            target_type: The target type

        Returns:
            The coerced value

        Raises:
            TypeError: If coercion is not safe or possible
        """
        if isinstance(value, target_type):
            return value

        # Handle None values - None can be assigned to any type
        # This allows for optional/nullable types in Dana
        if value is None:
            return None

        if not self.can_coerce(value, target_type):
            raise TypeError(f"Cannot safely coerce {type(value).__name__} to {target_type.__name__}")

        # Special case: bool to str (backward compatibility)
        if target_type is str and isinstance(value, bool):
            return "true" if value else "false"

        # Use enhanced semantic coercion with target type name
        target_type_name = target_type.__name__

        try:
            return self.semantic_coercer.coerce_value(value, target_type_name)
        except Exception as e:
            raise TypeError(f"Enhanced coercion failed for {type(value).__name__} to {target_type.__name__}: {e}")

    @staticmethod
    def coerce_binary_operands(left: Any, right: Any, operator: str) -> tuple[Any, Any]:
        """
        Coerce operands for binary operations using smart rules.

        Args:
            left: Left operand
            right: Right operand
            operator: The binary operator

        Returns:
            Tuple of (coerced_left, coerced_right)
        """
        # If types already match, no coercion needed
        if type(left) is type(right):
            return left, right

        # Create instance for coercion
        coercer = UnifiedTypeCoercion()

        # Numeric promotion: int + float → float + float
        if isinstance(left, int) and isinstance(right, float):
            return float(left), right
        if isinstance(left, float) and isinstance(right, int):
            return left, float(right)

        # String concatenation: allow number + string → string + string
        if operator == "+" and isinstance(left, int | float | bool) and isinstance(right, str):
            return coercer.coerce_value(left, str), right
        if operator == "+" and isinstance(left, str) and isinstance(right, int | float | bool):
            return left, coercer.coerce_value(right, str)

        # Comparison operations: allow cross-type comparisons with conversion
        if operator in ["==", "!=", "<", ">", "<=", ">="]:
            if isinstance(left, str) and isinstance(right, int | float):
                if coercer.can_coerce(left, type(right)):
                    return coercer.coerce_value(left, type(right)), right
            if isinstance(right, str) and isinstance(left, int | float):
                if coercer.can_coerce(right, type(left)):
                    return left, coercer.coerce_value(right, type(left))

        return left, right

    def coerce_to_bool(self, value: Any) -> bool:
        """
        Coerce a value to boolean using enhanced semantic rules.

        Args:
            value: The value to convert to boolean

        Returns:
            Boolean representation of the value
        """
        return self.semantic_coercer.coerce_to_bool(value)

    @staticmethod
    def coerce_llm_response(value: str) -> Any:
        """
        Intelligently coerce LLM responses to appropriate types.

        This method is kept for backward compatibility but now uses
        enhanced semantic coercion when possible.

        Args:
            value: The string response from an LLM function

        Returns:
            The value coerced to the most appropriate type
        """
        if not isinstance(value, str):
            return value

        # Use enhanced semantic coercion for smarter LLM response handling
        coercer = SemanticCoercer(strategy=CoercionStrategy.ENHANCED)

        # Strip whitespace for analysis
        cleaned = value.strip().lower()

        # Try boolean patterns first (enhanced semantic detection)
        try:
            # Convert standalone boolean-like responses
            if cleaned in ["yes", "no", "true", "false", "correct", "wrong", "right", "valid", "ok", "okay", "1", "0"]:
                return coercer.coerce_to_bool(value)
        except Exception:
            pass

        # Try numeric conversion for clearly numeric responses
        try:
            # Check if it's an integer
            if cleaned.isdigit() or (cleaned.startswith("-") and cleaned[1:].isdigit()):
                return int(cleaned)
            # Check if it's a float
            if any(c.isdigit() for c in cleaned) and ("." in cleaned or "e" in cleaned.lower()):
                return float(cleaned)
        except ValueError:
            pass

        # Return as string if no clear conversion
        return value

    def coerce_to_bool_smart(self, value: Any) -> bool:
        """
        Enhanced boolean coercion that handles LLM responses intelligently.

        Args:
            value: The value to convert to boolean

        Returns:
            Boolean representation of the value
        """
        return self.semantic_coercer.coerce_to_bool(value)

    @staticmethod
    def should_enable_coercion() -> bool:
        """
        Check if type coercion should be enabled based on configuration.

        Returns:
            True if coercion should be enabled
        """
        return os.environ.get("DANA_AUTO_COERCION", "1").lower() in ["1", "true", "yes", "y"]

    @staticmethod
    def should_enable_llm_coercion() -> bool:
        """
        Check if LLM-specific coercion should be enabled.

        Returns:
            True if LLM coercion should be enabled
        """
        return os.environ.get("DANA_LLM_AUTO_COERCION", "1").lower() in ["1", "true", "yes", "y"]


# Global instance for drop-in replacement
_unified_coercer = UnifiedTypeCoercion()


# Backward compatibility: Create TypeCoercion alias
class TypeCoercion:
    """
    Backward compatibility wrapper for the old TypeCoercion interface.

    All methods delegate to the unified enhanced coercion system.
    """

    @staticmethod
    def can_coerce(value: Any, target_type: type) -> bool:
        return _unified_coercer.can_coerce(value, target_type)

    @staticmethod
    def coerce_value(value: Any, target_type: type) -> Any:
        return _unified_coercer.coerce_value(value, target_type)

    @staticmethod
    def coerce_binary_operands(left: Any, right: Any, operator: str) -> tuple[Any, Any]:
        return _unified_coercer.coerce_binary_operands(left, right, operator)

    @staticmethod
    def coerce_to_bool(value: Any) -> bool:
        return _unified_coercer.coerce_to_bool(value)

    @staticmethod
    def coerce_llm_response(value: str) -> Any:
        return _unified_coercer.coerce_llm_response(value)

    @staticmethod
    def coerce_to_bool_smart(value: Any) -> bool:
        return _unified_coercer.coerce_to_bool_smart(value)

    @staticmethod
    def should_enable_coercion() -> bool:
        return _unified_coercer.should_enable_coercion()

    @staticmethod
    def should_enable_llm_coercion() -> bool:
        return _unified_coercer.should_enable_llm_coercion()
