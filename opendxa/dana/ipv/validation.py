"""
Enhanced type validation system for IPV.

This module provides the TypeValidator class with strict type checking,
automatic type conversion, and format-specific validation.
"""

import email.utils
import json
import re
from typing import Any
from urllib.parse import urlparse


class ValidationResult:
    """Result of a type validation operation."""

    def __init__(
        self, is_valid: bool, converted_value: Any = None, errors: list[str] | None = None, warnings: list[str] | None = None
    ):
        """
        Initialize validation result.

        Args:
            is_valid: Whether the validation passed
            converted_value: The converted/cleaned value
            errors: List of validation errors
            warnings: List of validation warnings
        """
        self.is_valid = is_valid
        self.converted_value = converted_value
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)


class TypeValidator:
    """
    Enhanced type validator with strict checking and automatic conversion.
    """

    def __init__(self):
        self._custom_validators: dict[type, callable] = {}
        self._format_validators: dict[str, callable] = {}

        # Register built-in format validators
        self._register_format_validators()

    def validate_and_convert(self, value: Any, target_type: type, validation_config: dict[str, Any] | None = None) -> ValidationResult:
        """
        Validate and convert a value to the target type.

        Args:
            value: Value to validate and convert
            target_type: Expected type
            validation_config: Type-specific validation configuration

        Returns:
            ValidationResult with conversion result and any errors/warnings
        """
        config = validation_config or {}

        # Handle None values
        if value is None:
            return self._handle_none_value(target_type, config)

        # Check if we have a custom validator for this type
        if target_type in self._custom_validators:
            return self._custom_validators[target_type](value, config)

        # Use built-in type validators
        if target_type == float:
            return self._validate_float(value, config)
        elif target_type == int:
            return self._validate_int(value, config)
        elif target_type == bool:
            return self._validate_bool(value, config)
        elif target_type == str:
            return self._validate_str(value, config)
        elif target_type == dict:
            return self._validate_dict(value, config)
        elif target_type == list:
            return self._validate_list(value, config)
        else:
            # Generic validation
            return self._validate_generic(value, target_type, config)

    def register_custom_validator(self, target_type: type, validator_func: callable) -> None:
        """Register a custom validator for a specific type."""
        self._custom_validators[target_type] = validator_func

    def register_format_validator(self, format_name: str, validator_func: callable) -> None:
        """Register a format-specific validator (e.g., 'email', 'url')."""
        self._format_validators[format_name] = validator_func

    def validate_format(self, value: str, format_name: str) -> ValidationResult:
        """Validate a string against a specific format."""
        if format_name not in self._format_validators:
            return ValidationResult(False, value, [f"Unknown format: {format_name}"])

        return self._format_validators[format_name](value)

    def _handle_none_value(self, target_type: type, config: dict[str, Any]) -> ValidationResult:
        """Handle None values based on type and configuration."""
        allow_none = config.get("allow_none", False)

        if allow_none:
            return ValidationResult(True, None)

        # Provide type-specific defaults
        defaults = {
            float: 0.0,
            int: 0,
            bool: False,
            str: "",
            dict: {},
            list: [],
        }

        if target_type in defaults:
            default_value = defaults[target_type]
            return ValidationResult(
                True, default_value, warnings=[f"None value converted to default {target_type.__name__}: {default_value}"]
            )

        return ValidationResult(False, None, [f"None value not allowed for type {target_type.__name__}"])

    def _validate_float(self, value: Any, config: dict[str, Any]) -> ValidationResult:
        """Validate and convert to float."""
        result = ValidationResult(True, value)

        # If already a float, check constraints
        if isinstance(value, float):
            result.converted_value = value
        elif isinstance(value, (int, bool)):
            result.converted_value = float(value)
        elif isinstance(value, str):
            # Clean and extract float from string
            result.converted_value = self._extract_float_from_string(value, config)
            if result.converted_value is None:
                result.add_error(f"Cannot convert string '{value}' to float")
                return result
        else:
            result.add_error(f"Cannot convert {type(value).__name__} to float")
            return result

        # Apply constraints
        self._apply_numeric_constraints(result, config)

        return result

    def _validate_int(self, value: Any, config: dict[str, Any]) -> ValidationResult:
        """Validate and convert to int."""
        result = ValidationResult(True, value)

        # If already an int, check constraints
        if isinstance(value, int) and not isinstance(value, bool):
            result.converted_value = value
        elif isinstance(value, bool):
            result.converted_value = int(value)
            result.add_warning("Boolean converted to integer")
        elif isinstance(value, float):
            if value.is_integer():
                result.converted_value = int(value)
            else:
                truncation_mode = config.get("decimal_truncation", "round")
                if truncation_mode == "round":
                    result.converted_value = round(value)
                elif truncation_mode == "floor":
                    result.converted_value = int(value)
                elif truncation_mode == "ceil":
                    import math

                    result.converted_value = math.ceil(value)
                else:
                    result.converted_value = int(value)
                result.add_warning(f"Float {value} converted to integer using {truncation_mode}")
        elif isinstance(value, str):
            # Extract integer from string
            result.converted_value = self._extract_int_from_string(value, config)
            if result.converted_value is None:
                result.add_error(f"Cannot convert string '{value}' to int")
                return result
        else:
            result.add_error(f"Cannot convert {type(value).__name__} to int")
            return result

        # Apply constraints
        self._apply_numeric_constraints(result, config)

        return result

    def _validate_bool(self, value: Any, config: dict[str, Any]) -> ValidationResult:
        """Validate and convert to bool."""
        result = ValidationResult(True, value)

        if isinstance(value, bool):
            result.converted_value = value
        elif isinstance(value, (int, float)):
            result.converted_value = bool(value)
            result.add_warning(f"Numeric value {value} converted to boolean")
        elif isinstance(value, str):
            result.converted_value = self._parse_bool_from_string(value, config)
            if result.converted_value is None:
                result.add_error(f"Cannot convert string '{value}' to bool - ambiguous value")
                return result
        else:
            result.add_error(f"Cannot convert {type(value).__name__} to bool")
            return result

        return result

    def _validate_str(self, value: Any, config: dict[str, Any]) -> ValidationResult:
        """Validate and convert to str."""
        result = ValidationResult(True, value)

        if isinstance(value, str):
            result.converted_value = value
        else:
            result.converted_value = str(value)
            result.add_warning(f"{type(value).__name__} converted to string")

        # Apply string cleaning
        if config.get("markdown_removal", False):
            result.converted_value = self._remove_markdown(result.converted_value)

        if config.get("whitespace_normalization", False):
            result.converted_value = self._normalize_whitespace(result.converted_value)

        # Apply format validation if specified
        format_name = config.get("format")
        if format_name:
            format_result = self.validate_format(result.converted_value, format_name)
            if not format_result.is_valid:
                result.errors.extend(format_result.errors)
                result.is_valid = False

        # Apply length constraints
        min_length = config.get("min_length")
        max_length = config.get("max_length")

        if min_length is not None and len(result.converted_value) < min_length:
            result.add_error(f"String length {len(result.converted_value)} is less than minimum {min_length}")

        if max_length is not None and len(result.converted_value) > max_length:
            result.add_error(f"String length {len(result.converted_value)} exceeds maximum {max_length}")

        return result

    def _validate_dict(self, value: Any, config: dict[str, Any]) -> ValidationResult:
        """Validate and convert to dict."""
        result = ValidationResult(True, value)

        if isinstance(value, dict):
            result.converted_value = value
        elif isinstance(value, str):
            # Try to parse as JSON
            try:
                result.converted_value = json.loads(value)
                if not isinstance(result.converted_value, dict):
                    result.add_error(f"JSON string parses to {type(result.converted_value).__name__}, not dict")
                    return result
            except json.JSONDecodeError as e:
                # Try to fix common JSON errors
                if config.get("error_correction", False):
                    fixed_json = self._fix_json_errors(value)
                    try:
                        result.converted_value = json.loads(fixed_json)
                        result.add_warning("JSON syntax errors were automatically corrected")
                    except json.JSONDecodeError:
                        result.add_error(f"Cannot parse string as JSON: {e}")
                        return result
                else:
                    result.add_error(f"Cannot parse string as JSON: {e}")
                    return result
        else:
            result.add_error(f"Cannot convert {type(value).__name__} to dict")
            return result

        # Apply schema validation if specified
        schema = config.get("schema")
        if schema:
            schema_result = self._validate_dict_schema(result.converted_value, schema)
            if not schema_result.is_valid:
                result.errors.extend(schema_result.errors)
                result.warnings.extend(schema_result.warnings)
                result.is_valid = False

        return result

    def _validate_list(self, value: Any, config: dict[str, Any]) -> ValidationResult:
        """Validate and convert to list."""
        result = ValidationResult(True, value)

        if isinstance(value, list):
            result.converted_value = value
        elif isinstance(value, (tuple, set)):
            result.converted_value = list(value)
            result.add_warning(f"{type(value).__name__} converted to list")
        elif isinstance(value, str):
            # Try to parse as JSON array
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    result.converted_value = parsed
                else:
                    result.add_error(f"JSON string parses to {type(parsed).__name__}, not list")
                    return result
            except json.JSONDecodeError:
                # Try to parse as bullet points or comma-separated
                if config.get("bullet_point_parsing", False):
                    result.converted_value = self._parse_bullet_points(value)
                elif config.get("comma_separated_parsing", False):
                    result.converted_value = [item.strip() for item in value.split(",")]
                else:
                    result.add_error("Cannot parse string as list")
                    return result
        else:
            # Convert single value to list
            result.converted_value = [value]
            result.add_warning(f"Single {type(value).__name__} converted to list")

        # Apply item type validation if specified
        item_type = config.get("item_type")
        if item_type:
            validated_items = []
            for i, item in enumerate(result.converted_value):
                item_result = self.validate_and_convert(item, item_type, config.get("item_config", {}))
                if item_result.is_valid:
                    validated_items.append(item_result.converted_value)
                    result.warnings.extend([f"Item {i}: {w}" for w in item_result.warnings])
                else:
                    result.errors.extend([f"Item {i}: {e}" for e in item_result.errors])
                    result.is_valid = False

            if result.is_valid:
                result.converted_value = validated_items

        return result

    def _validate_generic(self, value: Any, target_type: type, config: dict[str, Any]) -> ValidationResult:
        """Generic validation for unknown types."""
        result = ValidationResult(True, value)

        if isinstance(value, target_type):
            result.converted_value = value
        else:
            try:
                result.converted_value = target_type(value)
                result.add_warning(f"{type(value).__name__} converted to {target_type.__name__}")
            except (ValueError, TypeError) as e:
                result.add_error(f"Cannot convert {type(value).__name__} to {target_type.__name__}: {e}")

        return result

    def _extract_float_from_string(self, text: str, config: dict[str, Any]) -> float | None:
        """Extract float value from string, handling currency symbols and text."""
        # Remove currency symbols and common text
        cleaned = re.sub(r"[^\d\.\-\+]", "", text.strip())

        # Handle empty string
        if not cleaned:
            return config.get("fallback_value", 0.0)

        try:
            return float(cleaned)
        except ValueError:
            # Try to find the first number in the string
            match = re.search(r"[-+]?\d*\.?\d+", text)
            if match:
                try:
                    return float(match.group())
                except ValueError:
                    pass

            return None

    def _extract_int_from_string(self, text: str, config: dict[str, Any]) -> int | None:
        """Extract integer value from string, handling text numbers."""
        # First try direct conversion
        cleaned = re.sub(r"[^\d\-\+]", "", text.strip())

        if cleaned:
            try:
                return int(cleaned)
            except ValueError:
                pass

        # Try to handle text numbers
        text_numbers = {
            "zero": 0,
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
            "eleven": 11,
            "twelve": 12,
            "thirteen": 13,
            "fourteen": 14,
            "fifteen": 15,
            "sixteen": 16,
            "seventeen": 17,
            "eighteen": 18,
            "nineteen": 19,
            "twenty": 20,
        }

        text_lower = text.lower().strip()
        if text_lower in text_numbers:
            return text_numbers[text_lower]

        # Try to find the first number in the string
        match = re.search(r"[-+]?\d+", text)
        if match:
            try:
                return int(match.group())
            except ValueError:
                pass

        return None

    def _parse_bool_from_string(self, text: str, config: dict[str, Any]) -> bool | None:
        """Parse boolean value from string."""
        text_lower = text.lower().strip()

        # True values
        true_values = {"true", "yes", "y", "1", "on", "enabled", "active", "approved", "accept", "ok", "okay"}
        # False values
        false_values = {"false", "no", "n", "0", "off", "disabled", "inactive", "rejected", "deny", "cancel"}

        if text_lower in true_values:
            return True
        elif text_lower in false_values:
            return False

        # Check for conservative fallback
        conservative_fallback = config.get("conservative_fallback")
        if conservative_fallback is not None:
            return conservative_fallback

        return None  # Ambiguous

    def _apply_numeric_constraints(self, result: ValidationResult, config: dict[str, Any]) -> None:
        """Apply numeric constraints (min, max, range checking)."""
        if not result.is_valid:
            return

        value = result.converted_value

        # Min/max constraints
        min_value = config.get("min_value")
        max_value = config.get("max_value")

        if min_value is not None and value < min_value:
            result.add_error(f"Value {value} is less than minimum {min_value}")

        if max_value is not None and value > max_value:
            result.add_error(f"Value {value} exceeds maximum {max_value}")

        # Range checking for financial values
        if config.get("range_checking", False):
            if isinstance(value, float) and (value < -1e10 or value > 1e10):
                result.add_warning(f"Large financial value detected: {value}")

    def _remove_markdown(self, text: str) -> str:
        """Remove markdown formatting from text."""
        # Remove bold/italic markers
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # **bold**
        text = re.sub(r"\*(.*?)\*", r"\1", text)  # *italic*
        text = re.sub(r"__(.*?)__", r"\1", text)  # __bold__
        text = re.sub(r"_(.*?)_", r"\1", text)  # _italic_

        # Remove headers
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)

        # Remove bullet points
        text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)

        # Remove links
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

        return text.strip()

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        # Replace multiple whitespace with single space
        text = re.sub(r"\s+", " ", text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text

    def _fix_json_errors(self, json_str: str) -> str:
        """Attempt to fix common JSON syntax errors."""
        # Add quotes around unquoted keys
        json_str = re.sub(r"(\w+):", r'"\1":', json_str)

        # Fix single quotes to double quotes
        json_str = json_str.replace("'", '"')

        # Remove trailing commas
        json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)

        return json_str

    def _validate_dict_schema(self, data: dict, schema: dict[str, Any]) -> ValidationResult:
        """Validate dictionary against a schema."""
        result = ValidationResult(True, data)

        required_keys = schema.get("required", [])
        optional_keys = schema.get("optional", [])
        key_types = schema.get("key_types", {})

        # Check required keys
        for key in required_keys:
            if key not in data:
                result.add_error(f"Required key '{key}' is missing")

        # Check key types
        for key, expected_type in key_types.items():
            if key in data:
                value = data[key]
                if not isinstance(value, expected_type):
                    result.add_warning(f"Key '{key}' has type {type(value).__name__}, expected {expected_type.__name__}")

        return result

    def _parse_bullet_points(self, text: str) -> list[str]:
        """Parse bullet points from text into a list."""
        lines = text.split("\n")
        items = []

        for line in lines:
            line = line.strip()
            # Remove bullet point markers
            line = re.sub(r"^[-*+]\s*", "", line)
            if line:
                items.append(line)

        return items

    def _register_format_validators(self) -> None:
        """Register built-in format validators."""

        def validate_email(value: str) -> ValidationResult:
            """Validate email format."""
            try:
                # Use email.utils for basic validation
                parsed = email.utils.parseaddr(value)
                if "@" in parsed[1] and "." in parsed[1]:
                    return ValidationResult(True, value)
                else:
                    return ValidationResult(False, value, ["Invalid email format"])
            except Exception:
                return ValidationResult(False, value, ["Invalid email format"])

        def validate_url(value: str) -> ValidationResult:
            """Validate URL format."""
            try:
                result = urlparse(value)
                if result.scheme and result.netloc:
                    return ValidationResult(True, value)
                else:
                    return ValidationResult(False, value, ["Invalid URL format"])
            except Exception:
                return ValidationResult(False, value, ["Invalid URL format"])

        def validate_phone(value: str) -> ValidationResult:
            """Validate phone number format."""
            # Simple phone validation - digits, spaces, dashes, parentheses
            cleaned = re.sub(r"[^\d]", "", value)
            if 10 <= len(cleaned) <= 15:
                return ValidationResult(True, value)
            else:
                return ValidationResult(False, value, ["Invalid phone number format"])

        self.register_format_validator("email", validate_email)
        self.register_format_validator("url", validate_url)
        self.register_format_validator("phone", validate_phone)
