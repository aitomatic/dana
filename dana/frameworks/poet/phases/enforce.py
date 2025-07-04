"""
POET Enforce Phase - Output Validation and Enforcement

This module implements the Enforce (E) phase of the POET pipeline, responsible for:
1. Output validation and type checking
2. Post-processing and transformation
3. Domain-specific enforcement rules
4. Error handling and reporting

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass
from typing import Any

from dana.common.utils.logging import DANA_LOGGER
from dana.frameworks.poet.types import POETConfig


@dataclass
class EnforceResult:
    """Result of the Enforce phase."""

    output: Any = None
    context: dict[str, Any] = None
    validation_errors: list[str] = None
    is_valid: bool = True

    def add_error(self, error: str) -> None:
        """Add a validation error."""
        if self.validation_errors is None:
            self.validation_errors = []
        self.validation_errors.append(error)
        self.is_valid = False


class EnforcePhase:
    """Enforce phase implementation."""

    def __init__(self, config: POETConfig):
        """Initialize Enforce phase with configuration."""
        self.config = config
        self.logger = DANA_LOGGER.getLogger(__name__)

    def enforce(self, output: Any, context: dict[str, Any], expected_type: type | None = None) -> EnforceResult:
        """
        Validate and enforce output constraints.

        Args:
            output: The output to validate and enforce
            context: Execution context
            expected_type: Optional expected type for output validation

        Returns:
            EnforceResult with validated output and status
        """
        result = EnforceResult(output=output, context=context, validation_errors=[])

        try:
            # Validate context
            if context is None:
                result.add_error("Context cannot be None")
                return result

            # Basic output validation
            self._validate_output(result, expected_type)

            # Domain-specific enforcement if domain is specified
            if self.config.domain:
                self._enforce_domain_rules(result)

            # Post-processing
            self._post_process(result)

        except Exception as e:
            self.logger.error(f"Enforce phase failed: {e}")
            result.add_error(f"Enforce phase error: {e}")

        return result

    def _validate_output(self, result: EnforceResult, expected_type: type | None = None) -> None:
        """Validate output against constraints."""
        # Check for None output
        if result.output is None:
            result.add_error("Output cannot be None")

        # Type validation if expected_type is provided
        if expected_type is not None:
            if not isinstance(result.output, expected_type):
                result.add_error(f"Output type mismatch: expected {expected_type.__name__}, got {type(result.output).__name__}")

    def _enforce_domain_rules(self, result: EnforceResult) -> None:
        """Enforce domain-specific rules."""
        # TODO: Implement domain-specific enforcement rules
        # For now, just log that we would enforce domain rules
        self.logger.info(f"Would enforce domain rules for domain: {self.config.domain}")

    def _post_process(self, result: EnforceResult) -> None:
        """Post-process the output."""
        # TODO: Implement post-processing logic
        # For now, just log that we would post-process
        self.logger.info("Would post-process output")

    def validate_type(self, value: Any, expected_type: type) -> bool:
        """
        Validate if a value matches the expected type.

        Args:
            value: The value to validate
            expected_type: The expected type

        Returns:
            bool: True if value matches expected type, False otherwise
        """
        try:
            if not isinstance(value, expected_type):
                self.logger.warning(f"Type validation failed: expected {expected_type.__name__}, got {type(value).__name__}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Type validation error: {e}")
            return False

    def validate_range(self, value: int | float, min_val: int | float | None = None, max_val: int | float | None = None) -> bool:
        """
        Validate if a numeric value is within the specified range.

        Args:
            value: The value to validate
            min_val: Optional minimum value (inclusive)
            max_val: Optional maximum value (inclusive)

        Returns:
            bool: True if value is within range, False otherwise
        """
        try:
            if min_val is not None and value < min_val:
                self.logger.warning(f"Value {value} is below minimum {min_val}")
                return False
            if max_val is not None and value > max_val:
                self.logger.warning(f"Value {value} is above maximum {max_val}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Range validation error: {e}")
            return False
