"""
Enhanced Coercion Engine for Semantic Function Dispatch

This module provides intelligent type coercion that goes beyond simple Python type conversion
to include semantic understanding and context-aware behavior.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import re
from enum import Enum
from typing import Any

from dana.common.mixins.loggable import Loggable


class CoercionStrategy(Enum):
    """Available coercion strategies."""

    STRICT = "strict"  # Standard Python coercion only
    SEMANTIC = "semantic"  # Include semantic patterns
    CONTEXTUAL = "contextual"  # Context-aware coercion
    ENHANCED = "enhanced"  # All features enabled


class SemanticCoercer(Loggable):
    """Enhanced coercion engine with semantic understanding."""

    def __init__(self, strategy: CoercionStrategy = CoercionStrategy.ENHANCED):
        super().__init__()
        self.strategy = strategy
        self._boolean_patterns = self._build_boolean_patterns()
        self._numeric_patterns = self._build_numeric_patterns()

    def _build_boolean_patterns(self) -> dict[str, bool]:
        """Build semantic patterns for boolean coercion."""
        return {
            # Explicit boolean strings
            "true": True,
            "false": False,
            "yes": True,
            "no": False,
            "y": True,
            "n": False,
            "on": True,
            "off": False,
            "enabled": True,
            "disabled": False,
            "active": True,
            "inactive": False,
            # Conversational patterns
            "yeah": True,
            "nah": False,
            "yep": True,
            "nope": False,
            "sure": True,
            "never": False,
            "absolutely": True,
            "definitely not": False,
            "of course": True,
            "no way": False,
            "certainly": True,
            "not really": False,
            "indeed": True,
            "hardly": False,
            # Numeric zero patterns (CRITICAL FIX)
            "0": False,
            "0.0": False,
            "0.00": False,
            "zero": False,
            "none": False,
            "null": False,
            "empty": False,
            "blank": False,
            # Positive indicators
            "1": True,
            "positive": True,
            "good": True,
            "ok": True,
            "okay": True,
            "fine": True,
            "correct": True,
            "right": True,
        }

    def _build_numeric_patterns(self) -> dict[str, re.Pattern]:
        """Build regex patterns for numeric coercion."""
        return {
            "integer": re.compile(r"^[-+]?\d+$"),
            "float": re.compile(r"^[-+]?\d*\.?\d+([eE][-+]?\d+)?$"),
            "scientific": re.compile(r"^[-+]?\d*\.?\d+[eE][-+]?\d+$"),
            "currency": re.compile(r"^\$?(\d{1,3}(,\d{3})*|\d+)(\.\d{2})?$"),
            "percentage": re.compile(r"^(\d+\.?\d*)%$"),
        }

    def coerce_to_bool(self, value: Any, context: str | None = None) -> bool:
        """Enhanced boolean coercion with semantic understanding.

        Args:
            value: Value to coerce
            context: Optional context hint

        Returns:
            Boolean value
        """
        self.debug(f"Coercing to bool: {repr(value)} (context: {context})")

        # Handle None and actual booleans
        if value is None:
            return False
        if isinstance(value, bool):
            return value

        # Handle numeric values
        if isinstance(value, int | float):
            return value != 0

        # Handle strings with semantic patterns
        if isinstance(value, str):
            return self._coerce_string_to_bool(value.strip())

        # Fallback to Python's bool()
        return bool(value)

    def _coerce_string_to_bool(self, text: str) -> bool:
        """Coerce string to boolean using semantic patterns."""
        # Normalize text
        normalized = text.lower().strip()

        # Check semantic patterns first
        if self.strategy in [CoercionStrategy.SEMANTIC, CoercionStrategy.ENHANCED]:
            if normalized in self._boolean_patterns:
                result = self._boolean_patterns[normalized]
                self.debug(f"Semantic pattern match: '{text}' → {result}")
                return result

        # Check for contextual patterns
        if self.strategy in [CoercionStrategy.CONTEXTUAL, CoercionStrategy.ENHANCED]:
            contextual_result = self._apply_contextual_boolean_logic(normalized)
            if contextual_result is not None:
                self.debug(f"Contextual pattern match: '{text}' → {contextual_result}")
                return contextual_result

        # Enhanced zero handling (CRITICAL FIX)
        if self._is_zero_equivalent(normalized):
            self.debug(f"Zero equivalent detected: '{text}' → False")
            return False

        # Check for positive numeric strings
        if self._is_positive_numeric(normalized):
            self.debug(f"Positive numeric detected: '{text}' → True")
            return True

        # Fallback: empty strings are False, non-empty are True
        result = len(normalized) > 0
        self.debug(f"Fallback coercion: '{text}' → {result}")
        return result

    def _is_zero_equivalent(self, text: str) -> bool:
        """Check if text represents zero or false-like values."""
        zero_patterns = {"0", "0.0", "0.00", "0.000", "-0", "false", "f", "no", "n", "off", "null", "none", "nil", "empty", "blank"}
        return text in zero_patterns

    def _is_positive_numeric(self, text: str) -> bool:
        """Check if text represents a positive number."""
        try:
            num = float(text)
            return num > 0
        except ValueError:
            return False

    def _apply_contextual_boolean_logic(self, text: str) -> bool | None:
        """Apply contextual logic for boolean coercion."""
        # Question-like patterns
        if any(word in text for word in ["yes", "sure", "ok", "fine", "good"]):
            return True
        if any(word in text for word in ["no", "nope", "never", "bad", "wrong"]):
            return False

        # Sentiment-based patterns
        positive_indicators = ["great", "awesome", "perfect", "excellent", "wonderful"]
        negative_indicators = ["terrible", "awful", "horrible", "bad", "wrong"]

        if any(word in text for word in positive_indicators):
            return True
        if any(word in text for word in negative_indicators):
            return False

        return None

    def coerce_value(self, value: Any, target_type: str, context: str | None = None) -> Any:
        """Main coercion entry point.

        Args:
            value: Value to coerce
            target_type: Target type name ("bool", "int", "float", "str", "dict", "list", or Dana struct name)
            context: Optional context hint

        Returns:
            Coerced value

        Raises:
            ValueError: If coercion is not possible
        """
        self.debug(f"Coercing {repr(value)} to {target_type} (context: {context})")

        # Extract final answer from FINAL_ANSWER: format if present
        if isinstance(value, str):
            extracted_value = self._extract_final_answer(value)
            if extracted_value != value:
                self.debug(f"Extracted final answer: {repr(value)} → {repr(extracted_value)}")
                value = extracted_value

        if target_type == "bool":
            return self.coerce_to_bool(value, context)
        elif target_type == "int":
            return int(float(value)) if isinstance(value, str) and "." in value else int(value)
        elif target_type == "float":
            return float(value)
        elif target_type == "str":
            return str(value)
        elif target_type == "dict":
            return self._coerce_to_dict(value, context)
        elif target_type == "list":
            return self._coerce_to_list(value, context)
        else:
            # Check if this is a custom Dana struct type
            coerced_struct = self._try_coerce_to_struct(value, target_type, context)
            if coerced_struct is not None:
                return coerced_struct

            # For unknown types, return as-is
            self.debug(f"Unknown target type '{target_type}', returning value as-is")
            return value

    def _coerce_to_dict(self, value: Any, context: str | None = None) -> dict:
        """Coerce value to dictionary.

        Args:
            value: Value to coerce
            context: Optional context hint

        Returns:
            Dictionary value

        Raises:
            ValueError: If coercion is not possible
        """
        self.debug(f"Coercing to dict: {repr(value)} (context: {context})")

        # If already a dict, return as-is
        if isinstance(value, dict):
            return value

        # Try to parse JSON string
        if isinstance(value, str):
            import json

            try:
                # Clean up markdown code fences if present
                cleaned_value = self._clean_json_string(value)
                result = json.loads(cleaned_value)
                if isinstance(result, dict):
                    self.debug("Successfully parsed JSON string to dict")
                    return result
                else:
                    raise ValueError(f"JSON parsed to {type(result)} instead of dict")
            except json.JSONDecodeError as e:
                raise ValueError(f"Cannot parse string as JSON dict: {e}")

        # For other types, try to convert if they have dict-like methods
        if hasattr(value, "items"):
            return dict(value)

        raise ValueError(f"Cannot coerce {type(value).__name__} to dict")

    def _coerce_to_list(self, value: Any, context: str | None = None) -> list:
        """Coerce value to list.

        Args:
            value: Value to coerce
            context: Optional context hint

        Returns:
            List value

        Raises:
            ValueError: If coercion is not possible
        """
        self.debug(f"Coercing to list: {repr(value)} (context: {context})")

        # If already a list, return as-is
        if isinstance(value, list):
            return value

        # Try to parse JSON string
        if isinstance(value, str):
            import json

            try:
                # Clean up markdown code fences if present
                cleaned_value = self._clean_json_string(value)
                result = json.loads(cleaned_value)
                if isinstance(result, list):
                    self.debug("Successfully parsed JSON string to list")
                    return result
                else:
                    raise ValueError(f"JSON parsed to {type(result)} instead of list")
            except json.JSONDecodeError as e:
                raise ValueError(f"Cannot parse string as JSON list: {e}")

        # For other iterables (except strings), convert to list
        if hasattr(value, "__iter__") and not isinstance(value, str | bytes):
            return list(value)

        raise ValueError(f"Cannot coerce {type(value).__name__} to list")

    def _extract_final_answer(self, text: str) -> str:
        """Extract final answer from FINAL_ANSWER: format if present."""
        if "FINAL_ANSWER:" not in text:
            return text

        # Look for the final answer marker
        final_answer_index = text.find("FINAL_ANSWER:")
        if final_answer_index == -1:
            return text

        # Extract everything after FINAL_ANSWER:
        answer_part = text[final_answer_index + len("FINAL_ANSWER:") :].strip()

        # If the answer is empty, return original text
        if not answer_part:
            return text

        return answer_part

    def _try_coerce_to_struct(self, value: Any, target_type: str, context: str | None = None) -> Any | None:
        """Try to coerce a value to a Dana struct type.

        Args:
            value: Value to coerce (usually a string from LLM)
            target_type: Target struct type name
            context: Optional context hint

        Returns:
            StructInstance if coercion successful, None if not applicable

        Raises:
            ValueError: If coercion fails for a valid struct type
        """
        try:
            # Import here to avoid circular imports
            from dana.registry import TYPE_REGISTRY

            # Check if this is a registered Dana struct type
            if not TYPE_REGISTRY.exists(target_type):
                self.debug(f"'{target_type}' is not a registered struct type")
                return None

            self.debug(f"Found registered struct type: {target_type}")

            # If value is already a struct instance of the correct type, return it
            from dana.core.builtin_types.struct_system import StructInstance

            if isinstance(value, StructInstance) and value.struct_type.name == target_type:
                self.debug(f"Value is already a {target_type} struct instance")
                return value

            # Try to coerce from string (common case for LLM responses)
            if isinstance(value, str):
                return self._coerce_string_to_struct(value, target_type, context)

            # Try to coerce from dict (already parsed JSON)
            elif isinstance(value, dict):
                return self._coerce_dict_to_struct(value, target_type, context)

            # Try to coerce from list (unlikely but possible)
            elif isinstance(value, list):
                self.debug(f"Cannot coerce list to struct {target_type} - structs require object/dict data")
                raise ValueError(f"Cannot coerce list to struct {target_type}")

            else:
                self.debug(f"Cannot coerce {type(value).__name__} to struct {target_type}")
                raise ValueError(f"Cannot coerce {type(value).__name__} to struct {target_type}")

        except Exception as e:
            if "not a registered struct type" in str(e):
                # Not a struct type, return None to fall through
                return None
            else:
                # Actual coercion error for a valid struct type
                self.debug(f"Struct coercion failed for {target_type}: {e}")
                raise ValueError(f"Failed to coerce value to struct {target_type}: {e}")

    def _coerce_string_to_struct(self, text: str, target_type: str, context: str | None = None) -> Any:
        """Coerce string (usually JSON) to Dana struct instance.

        Args:
            text: String to parse (usually JSON from LLM)
            target_type: Target struct type name
            context: Optional context hint

        Returns:
            StructInstance

        Raises:
            ValueError: If parsing or validation fails
        """
        import json

        # Clean up the text - remove common LLM artifacts
        cleaned_text = text.strip()

        # Remove markdown code fences if present
        if cleaned_text.startswith("```"):
            lines = cleaned_text.split("\n")
            # Remove first line (```json or similar)
            if len(lines) > 1:
                lines = lines[1:]
            # Remove last line if it's just ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        self.debug(f"Cleaned text for struct parsing: {cleaned_text[:100]}...")

        try:
            # Parse as JSON
            json_data = json.loads(cleaned_text)
            self.debug(f"Successfully parsed JSON: {json_data}")

            # Create struct instance from JSON
            return self._coerce_dict_to_struct(json_data, target_type, context)

        except json.JSONDecodeError as e:
            self.debug(f"JSON parsing failed: {e}")
            raise ValueError(f"Invalid JSON for struct {target_type}: {e}")

    def _coerce_dict_to_struct(self, data: dict, target_type: str, context: str | None = None) -> Any:
        """Coerce dictionary to Dana struct instance.

        Args:
            data: Dictionary data to convert
            target_type: Target struct type name
            context: Optional context hint

        Returns:
            StructInstance

        Raises:
            ValueError: If validation fails
        """
        from dana.registry import TYPE_REGISTRY

        try:
            # Use the registry method to create instance from JSON
            struct_instance = TYPE_REGISTRY.create_instance_from_json(data, target_type)
            self.debug(f"Successfully created {target_type} instance: {struct_instance}")
            return struct_instance

        except ValueError as e:
            self.debug(f"Struct validation failed for {target_type}: {e}")
            raise ValueError(f"Struct validation failed for {target_type}: {e}")

    def _clean_json_string(self, value: str) -> str:
        """Clean JSON string by removing markdown code fences and extra whitespace.

        Args:
            value: Raw string that might contain JSON

        Returns:
            Cleaned JSON string
        """
        import re

        # Remove markdown code fences (```json ... ``` or ``` ... ```)
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", value.strip(), flags=re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned, flags=re.MULTILINE)

        # Remove any leading/trailing whitespace
        cleaned = cleaned.strip()

        self.debug(f"Cleaned JSON: {repr(value)} → {repr(cleaned)}")
        return cleaned

    def test_semantic_equivalence(self, left: Any, right: Any) -> bool:
        """Test semantic equivalence between values.

        This implements enhanced equality that considers semantic meaning.
        Examples: "0" == False, "1" == True, "yes" == True
        """
        self.debug(f"Testing semantic equivalence: {repr(left)} == {repr(right)}")

        # Try coercing both to boolean and compare
        try:
            left_bool = self.coerce_to_bool(left)
            right_bool = self.coerce_to_bool(right)
            if left_bool == right_bool:
                self.debug(f"Boolean equivalence: {left_bool}")
                return True
        except (ValueError, TypeError):
            pass

        # Fallback to standard equality
        return left == right


# Convenience functions and global instance
_global_coercer = SemanticCoercer()


def coerce_value(value: Any, target_type: str, context: str | None = None) -> Any:
    """Convenience function for value coercion."""
    return _global_coercer.coerce_value(value, target_type, context)


def semantic_bool(value: Any) -> bool:
    """Convenience function for semantic boolean coercion."""
    return _global_coercer.coerce_to_bool(value)


def semantic_equals(left: Any, right: Any) -> bool:
    """Convenience function for semantic equality testing."""
    return _global_coercer.test_semantic_equivalence(left, right)
