"""
POE-Specific Error Types

This module defines error types for the POE (Perceive → Operate → Enforce) pipeline,
providing clear error categorization and better debugging capabilities.
"""

from typing import Any, Dict, Optional


class POEError(Exception):
    """Base class for all POE pipeline errors."""

    def __init__(self, message: str, stage: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize POE error.

        Args:
            message: Human-readable error description
            stage: POE stage where error occurred ('perceive', 'operate', 'enforce', 'train')
            context: Additional context information about the error
        """
        super().__init__(message)
        self.stage = stage
        self.context = context or {}

    def __str__(self) -> str:
        context_str = f" | Context: {self.context}" if self.context else ""
        return f"[{self.stage.upper()} Stage] {super().__str__()}{context_str}"


class PerceiveError(POEError):
    """Error during the Perceive stage (input processing)."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "perceive", context)


class OperateError(POEError):
    """Error during the Operate stage (function execution)."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "operate", context)


class EnforceError(POEError):
    """Error during the Enforce stage (output validation)."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "enforce", context)


class TrainError(POEError):
    """Error during the optional Train stage (learning/optimization)."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "train", context)


# Specific error types for common failure scenarios


class DomainPluginError(PerceiveError):
    """Error loading or executing domain plugin."""

    def __init__(self, domain: str, reason: str, context: Optional[Dict[str, Any]] = None):
        message = f"Domain plugin '{domain}' failed: {reason}"
        super().__init__(message, context)
        self.domain = domain
        self.reason = reason


class InputValidationError(PerceiveError):
    """Error validating or processing inputs."""

    def __init__(self, input_type: str, reason: str, context: Optional[Dict[str, Any]] = None):
        message = f"Input validation failed for {input_type}: {reason}"
        super().__init__(message, context)
        self.input_type = input_type
        self.reason = reason


class RetryExhaustedError(OperateError):
    """Error when all retry attempts are exhausted."""

    def __init__(self, attempts: int, last_error: Exception, context: Optional[Dict[str, Any]] = None):
        message = f"All {attempts} retry attempts failed. Last error: {last_error}"
        super().__init__(message, context)
        self.attempts = attempts
        self.last_error = last_error


class TimeoutError(OperateError):
    """Error when function execution exceeds timeout."""

    def __init__(self, timeout: float, actual_time: float, context: Optional[Dict[str, Any]] = None):
        message = f"Function execution timeout: {actual_time:.2f}s > {timeout:.2f}s"
        super().__init__(message, context)
        self.timeout = timeout
        self.actual_time = actual_time


class OutputValidationError(EnforceError):
    """Error validating function output."""

    def __init__(self, expected_type: str, actual_type: str, reason: str, context: Optional[Dict[str, Any]] = None):
        message = f"Output validation failed: expected {expected_type}, got {actual_type}. {reason}"
        super().__init__(message, context)
        self.expected_type = expected_type
        self.actual_type = actual_type
        self.reason = reason


class ParameterLearningError(TrainError):
    """Error during parameter learning and optimization."""

    def __init__(self, parameter: str, reason: str, context: Optional[Dict[str, Any]] = None):
        message = f"Parameter learning failed for '{parameter}': {reason}"
        super().__init__(message, context)
        self.parameter = parameter
        self.reason = reason


class ConfigurationError(POEError):
    """Error in POE configuration or setup."""

    def __init__(self, config_item: str, reason: str, context: Optional[Dict[str, Any]] = None):
        message = f"Configuration error for '{config_item}': {reason}"
        super().__init__(message, "configuration", context)
        self.config_item = config_item
        self.reason = reason


# Utility functions for error handling


def wrap_poe_error(func_name: str, stage: str, original_error: Exception, context: Optional[Dict[str, Any]] = None) -> POEError:
    """
    Wrap a generic exception as a POE-specific error.

    Args:
        func_name: Name of the function where error occurred
        stage: POE stage ('perceive', 'operate', 'enforce', 'train')
        original_error: Original exception that was caught
        context: Additional context information

    Returns:
        POE-specific error instance
    """
    error_context = context or {}
    error_context.update(
        {"function_name": func_name, "original_error_type": type(original_error).__name__, "original_error_message": str(original_error)}
    )

    message = f"Error in function '{func_name}': {original_error}"

    # Map to appropriate POE error type
    error_map = {"perceive": PerceiveError, "operate": OperateError, "enforce": EnforceError, "train": TrainError}

    error_class = error_map.get(stage, POEError)
    return error_class(message, error_context)


def create_context(
    function_name: Optional[str] = None,
    domain: Optional[str] = None,
    attempt: Optional[int] = None,
    execution_time: Optional[float] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Create standardized context dictionary for POE errors.

    Args:
        function_name: Name of the function being executed
        domain: Domain plugin being used
        attempt: Current retry attempt number
        execution_time: Time taken for execution
        **kwargs: Additional context items

    Returns:
        Dictionary with context information
    """
    context = {}

    if function_name:
        context["function_name"] = function_name
    if domain:
        context["domain"] = domain
    if attempt:
        context["attempt"] = attempt
    if execution_time:
        context["execution_time"] = execution_time

    context.update(kwargs)
    return context
