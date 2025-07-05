"""Validation utilities for Dana.

This module provides centralized validation utilities to eliminate code duplication
across the Dana codebase. All validation functions follow consistent patterns
and provide clear, actionable error messages.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import os
from pathlib import Path
from typing import Any, TypeVar

from dana.common.exceptions import DanaError
from dana.common.utils.logging import DANA_LOGGER

T = TypeVar("T")


class ValidationError(DanaError):
    """Error raised when validation fails."""

    def __init__(self, message: str, field_name: str | None = None, value: Any = None):
        """Initialize validation error.

        Args:
            message: Error message
            field_name: Name of the field that failed validation
            value: The value that failed validation
        """
        super().__init__(message)
        self.field_name = field_name
        self.value = value


class ValidationUtilities:
    """Centralized validation utilities for Dana.

    This class provides static methods for common validation patterns used
    throughout the Dana codebase. All methods follow consistent error
    reporting and logging patterns.
    """

    @staticmethod
    def validate_required_field(value: Any, field_name: str, context: str = "") -> None:
        """Validate that a required field has a value.

        Args:
            value: The value to check
            field_name: Name of the field being validated
            context: Optional context for better error messages

        Raises:
            ValidationError: If the field is None, empty string, or empty collection
        """
        if value is None:
            raise ValidationError(
                f"Required field '{field_name}' is missing{f' in {context}' if context else ''}", field_name=field_name, value=value
            )

        if isinstance(value, str) and not value.strip():
            raise ValidationError(
                f"Required field '{field_name}' cannot be empty{f' in {context}' if context else ''}", field_name=field_name, value=value
            )

        if isinstance(value, list | dict | set) and len(value) == 0:
            raise ValidationError(
                f"Required field '{field_name}' cannot be empty{f' in {context}' if context else ''}", field_name=field_name, value=value
            )

    @staticmethod
    def validate_type(value: Any, expected_type: type[T], field_name: str, context: str = "") -> T:
        """Validate that a value has the expected type.

        Args:
            value: The value to check
            expected_type: The expected type
            field_name: Name of the field being validated
            context: Optional context for better error messages

        Returns:
            The value cast to the expected type

        Raises:
            ValidationError: If the value is not of the expected type
        """
        if value is not None and not isinstance(value, expected_type):
            raise ValidationError(
                f"Field '{field_name}' must be of type {expected_type.__name__}, got {type(value).__name__}{f' in {context}' if context else ''}",
                field_name=field_name,
                value=value,
            )
        return value

    @staticmethod
    def validate_enum(value: Any, valid_values: list[Any], field_name: str, context: str = "") -> Any:
        """Validate that a value is in a list of valid values.

        Args:
            value: The value to check
            valid_values: List of valid values
            field_name: Name of the field being validated
            context: Optional context for better error messages

        Returns:
            The validated value

        Raises:
            ValidationError: If the value is not in the valid values list
        """
        if value is not None and value not in valid_values:
            raise ValidationError(
                f"Field '{field_name}' must be one of {valid_values}, got '{value}'{f' in {context}' if context else ''}",
                field_name=field_name,
                value=value,
            )
        return value

    @staticmethod
    def validate_numeric_range(
        value: float | int,
        min_val: float | int | None = None,
        max_val: float | int | None = None,
        field_name: str = "value",
        context: str = "",
    ) -> float | int:
        """Validate that a numeric value is within a specified range.

        Args:
            value: The numeric value to check
            min_val: Minimum allowed value (inclusive)
            max_val: Maximum allowed value (inclusive)
            field_name: Name of the field being validated
            context: Optional context for better error messages

        Returns:
            The validated value

        Raises:
            ValidationError: If the value is outside the specified range
        """
        if not isinstance(value, int | float):
            raise ValidationError(
                f"Field '{field_name}' must be numeric, got {type(value).__name__}{f' in {context}' if context else ''}",
                field_name=field_name,
                value=value,
            )

        if min_val is not None and value < min_val:
            raise ValidationError(
                f"Field '{field_name}' must be >= {min_val}, got {value}{f' in {context}' if context else ''}",
                field_name=field_name,
                value=value,
            )

        if max_val is not None and value > max_val:
            raise ValidationError(
                f"Field '{field_name}' must be <= {max_val}, got {value}{f' in {context}' if context else ''}",
                field_name=field_name,
                value=value,
            )

        return value

    @staticmethod
    def validate_path(
        path: str | Path,
        must_exist: bool = True,
        must_be_file: bool = False,
        must_be_dir: bool = False,
        field_name: str = "path",
        context: str = "",
    ) -> Path:
        """Validate that a path is valid and optionally exists.

        Args:
            path: The path to validate
            must_exist: Whether the path must exist
            must_be_file: Whether the path must be a file (only checked if must_exist=True)
            must_be_dir: Whether the path must be a directory (only checked if must_exist=True)
            field_name: Name of the field being validated
            context: Optional context for better error messages

        Returns:
            The validated Path object

        Raises:
            ValidationError: If the path is invalid or doesn't meet requirements
        """
        try:
            path_obj = Path(path)
        except Exception as e:
            raise ValidationError(
                f"Field '{field_name}' is not a valid path: {e}{f' in {context}' if context else ''}", field_name=field_name, value=path
            )

        if must_exist and not path_obj.exists():
            raise ValidationError(
                f"Path '{path_obj}' does not exist{f' in {context}' if context else ''}", field_name=field_name, value=path
            )

        if must_exist and must_be_file and not path_obj.is_file():
            raise ValidationError(
                f"Path '{path_obj}' must be a file{f' in {context}' if context else ''}", field_name=field_name, value=path
            )

        if must_exist and must_be_dir and not path_obj.is_dir():
            raise ValidationError(
                f"Path '{path_obj}' must be a directory{f' in {context}' if context else ''}", field_name=field_name, value=path
            )

        return path_obj

    @staticmethod
    def validate_config_structure(
        config: dict[str, Any],
        required_keys: list[str] | None = None,
        optional_keys: list[str] | None = None,
        allow_extra_keys: bool = True,
        context: str = "",
    ) -> dict[str, Any]:
        """Validate the structure of a configuration dictionary.

        Args:
            config: The configuration dictionary to validate
            required_keys: List of required keys
            optional_keys: List of optional keys
            allow_extra_keys: Whether to allow keys not in required/optional lists
            context: Optional context for better error messages

        Returns:
            The validated configuration dictionary

        Raises:
            ValidationError: If the configuration structure is invalid
        """
        if not isinstance(config, dict):
            raise ValidationError(
                f"Configuration must be a dictionary, got {type(config).__name__}{f' in {context}' if context else ''}",
                field_name="config",
                value=config,
            )

        # Check required keys
        if required_keys:
            for key in required_keys:
                if key not in config:
                    raise ValidationError(
                        f"Required configuration key '{key}' is missing{f' in {context}' if context else ''}", field_name=key, value=None
                    )

        # Check for unexpected keys if not allowing extra keys
        if not allow_extra_keys:
            allowed_keys = set(required_keys or []) | set(optional_keys or [])
            extra_keys = set(config.keys()) - allowed_keys
            if extra_keys:
                raise ValidationError(
                    f"Unexpected configuration keys: {sorted(extra_keys)}{f' in {context}' if context else ''}. "
                    f"Allowed keys: {sorted(allowed_keys)}",
                    field_name="config",
                    value=config,
                )

        return config

    @staticmethod
    def validate_model_availability(
        model_name: str, available_models: list[str] | None = None, required_env_vars: list[str] | None = None, context: str = ""
    ) -> bool:
        """Validate that a model is available for use.

        Args:
            model_name: Name of the model to validate
            available_models: List of available model names (if None, only check env vars)
            required_env_vars: List of environment variables required for this model
            context: Optional context for better error messages

        Returns:
            True if the model is available, False otherwise

        Raises:
            ValidationError: If model_name is invalid
        """
        ValidationUtilities.validate_required_field(model_name, "model_name")

        # Debug logging to understand model validation
        DANA_LOGGER.debug(f"Validating model '{model_name}' with required_env_vars: {required_env_vars}")

        # Check if model is in available models list (if provided)
        if available_models is not None and model_name not in available_models:
            DANA_LOGGER.debug(f"Model '{model_name}' not in available models list: {available_models}")
            return False

        # Check required environment variables
        if required_env_vars:
            missing_vars = []
            for var in required_env_vars:
                value = os.getenv(var)
                if not value:
                    missing_vars.append(var)
                else:
                    DANA_LOGGER.debug(f"Environment variable '{var}' is set for model '{model_name}'")

            if missing_vars:
                DANA_LOGGER.debug(f"Model '{model_name}' missing environment variables: {missing_vars}")
                return False

        DANA_LOGGER.debug(f"Model '{model_name}' validation passed")
        return True

    @staticmethod
    def validate_decay_parameters(decay_rate: float, decay_interval: int, context: str = "") -> tuple[float, int]:
        """Validate decay parameters for memory systems.

        Args:
            decay_rate: The decay rate (must be between 0 and 1)
            decay_interval: The decay interval in seconds (must be positive)
            context: Optional context for better error messages

        Returns:
            Tuple of (validated_decay_rate, validated_decay_interval)

        Raises:
            ValidationError: If parameters are invalid
        """
        # Allow decay_rate of 0 for permanent memory
        if decay_rate != 0:
            ValidationUtilities.validate_numeric_range(decay_rate, min_val=0.0, max_val=1.0, field_name="decay_rate", context=context)

        ValidationUtilities.validate_numeric_range(
            decay_interval,
            min_val=1,
            field_name="decay_interval",
            context=context,  # At least 1 second
        )

        # Warn about potentially problematic combinations
        if decay_rate > 0 and decay_rate < 1:
            import math

            half_life = -math.log(2) / math.log(1 - decay_rate)
            expected_interval = decay_interval / half_life

            if expected_interval > 10:
                DANA_LOGGER.warning(
                    f"Decay interval ({decay_interval}s) seems long relative to decay rate "
                    f"({decay_rate}). Memory will take {expected_interval:.1f} intervals to reach half-life{f' in {context}' if context else ''}"
                )
            elif expected_interval < 0.1:
                DANA_LOGGER.warning(
                    f"Decay interval ({decay_interval}s) seems short relative to decay rate "
                    f"({decay_rate}). Memory will reach half-life in {expected_interval:.1f} intervals{f' in {context}' if context else ''}"
                )

        return decay_rate, decay_interval
