"""Error formatting utilities for Dana.

This module provides centralized error message formatting utilities that follow
the Dana error message standard format:

"[What failed]: [Why it failed]. [What user can do]. [Available alternatives]"

Classes:
    ErrorFormattingUtilities: Static utility class for formatting standardized error messages

Example:
    >>> from dana.common.utils.error_formatting import ErrorFormattingUtilities
    >>>
    >>> # Resource error
    >>> error_msg = ErrorFormattingUtilities.format_resource_error(
    ...     resource_name="llm_model",
    ...     reason="missing API key",
    ...     action="set OPENAI_API_KEY environment variable",
    ...     alternatives=["use local model", "configure alternative provider"]
    ... )
    >>> print(error_msg)
    "Resource 'llm_model' unavailable: missing API key. Set OPENAI_API_KEY environment variable. Available alternatives: use local model, configure alternative provider"
"""

from typing import Any

from dana.common.utils.logging import DANA_LOGGER


class ErrorFormattingUtilities:
    """Utility class for standardized error message formatting.

    All methods follow the Dana error message format:
    "[What failed]: [Why it failed]. [What user can do]. [Available alternatives]"

    This ensures consistent, actionable error messages across the entire codebase.
    """

    @staticmethod
    def format_resource_error(
        resource_name: str, reason: str, action: str | None = None, alternatives: list[str] | None = None, context: str = ""
    ) -> str:
        """Format a resource-related error message.

        Args:
            resource_name: Name of the resource that failed
            reason: Why the resource failed
            action: What the user can do to fix it
            alternatives: List of alternative options
            context: Optional context for additional information

        Returns:
            Formatted error message following Dana standard

        Example:
            >>> ErrorFormattingUtilities.format_resource_error(
            ...     resource_name="database",
            ...     reason="connection timeout",
            ...     action="check network connectivity",
            ...     alternatives=["use backup database", "retry with increased timeout"]
            ... )
            "Resource 'database' unavailable: connection timeout. Check network connectivity. Available alternatives: use backup database, retry with increased timeout"
        """
        context_suffix = f" in {context}" if context else ""

        # What failed
        what_failed = f"Resource '{resource_name}' unavailable"

        # Why it failed
        why_failed = reason

        # What user can do
        user_action = action if action else "check resource configuration and try again"

        # Available alternatives
        alternatives_text = ""
        if alternatives:
            alternatives_text = f" Available alternatives: {', '.join(alternatives)}"

        # Capitalize only the first letter if it's lowercase, preserve the rest
        if user_action and user_action[0].islower():
            user_action = user_action[0].upper() + user_action[1:]

        return f"{what_failed}: {why_failed}{context_suffix}. {user_action}.{alternatives_text}"

    @staticmethod
    def format_validation_error(field_name: str, value: Any, reason: str, expected: str | None = None, context: str = "") -> str:
        """Format a validation error message.

        Args:
            field_name: Name of the field that failed validation
            value: The invalid value
            reason: Why the value is invalid
            expected: What was expected instead
            context: Optional context for additional information

        Returns:
            Formatted error message following Dana standard

        Example:
            >>> ErrorFormattingUtilities.format_validation_error(
            ...     field_name="temperature",
            ...     value=150,
            ...     reason="value exceeds maximum",
            ...     expected="value between 0 and 100"
            ... )
            "Field 'temperature' validation failed: value exceeds maximum (got 150). Provide value between 0 and 100. Check field requirements and valid ranges"
        """
        context_suffix = f" in {context}" if context else ""

        # What failed
        what_failed = f"Field '{field_name}' validation failed"

        # Why it failed
        why_failed = f"{reason} (got {value})"

        # What user can do
        if expected:
            user_action = f"provide {expected}"
        else:
            user_action = "check field requirements and provide valid value"

            # Available alternatives
        alternatives_text = " Check field requirements and valid ranges"

        # Capitalize only the first letter if it's lowercase, preserve the rest
        if user_action and user_action[0].islower():
            user_action = user_action[0].upper() + user_action[1:]

        return f"{what_failed}: {why_failed}{context_suffix}. {user_action}.{alternatives_text}"

    @staticmethod
    def format_configuration_error(config_key: str, issue: str, solution: str | None = None, config_file: str | None = None) -> str:
        """Format a configuration error message.

        Args:
            config_key: Configuration key that has an issue
            issue: Description of the configuration issue
            solution: Suggested solution
            config_file: Configuration file name if applicable

        Returns:
            Formatted error message following Dana standard

        Example:
            >>> ErrorFormattingUtilities.format_configuration_error(
            ...     config_key="llm.model",
            ...     issue="not found in configuration file",
            ...     solution="add model configuration to dana_config.json",
            ...     config_file="dana_config.json"
            ... )
            "Configuration 'llm.model' invalid: not found in configuration file 'dana_config.json'. Add model configuration to dana_config.json. Check configuration file format and required keys"
        """
        file_suffix = f" '{config_file}'" if config_file else ""

        # What failed
        what_failed = f"Configuration '{config_key}' invalid"

        # Why it failed
        why_failed = f"{issue}{file_suffix}"

        # What user can do
        if solution:
            user_action = solution
        else:
            user_action = "check configuration format and provide valid value"

            # Available alternatives
        alternatives_text = " Check configuration file format and required keys"

        # Capitalize only the first letter if it's lowercase, preserve the rest
        if user_action and user_action[0].islower():
            user_action = user_action[0].upper() + user_action[1:]

        return f"{what_failed}: {why_failed}. {user_action}.{alternatives_text}"

    @staticmethod
    def format_llm_error(
        operation: str, reason: str, model_name: str | None = None, suggestion: str | None = None, available_models: list[str] | None = None
    ) -> str:
        """Format an LLM-related error message.

        Args:
            operation: The LLM operation that failed
            reason: Why the operation failed
            model_name: Name of the model if applicable
            suggestion: Suggested fix
            available_models: List of available models

        Returns:
            Formatted error message following Dana standard

        Example:
            >>> ErrorFormattingUtilities.format_llm_error(
            ...     operation="model initialization",
            ...     reason="API key not found",
            ...     model_name="gpt-4",
            ...     suggestion="set OPENAI_API_KEY environment variable",
            ...     available_models=["gpt-3.5-turbo", "claude-3"]
            ... )
            "LLM model initialization failed: API key not found for model 'gpt-4'. Set OPENAI_API_KEY environment variable. Available models: gpt-3.5-turbo, claude-3"
        """
        model_suffix = f" for model '{model_name}'" if model_name else ""

        # What failed
        what_failed = f"LLM {operation} failed"

        # Why it failed
        why_failed = f"{reason}{model_suffix}"

        # What user can do
        if suggestion:
            user_action = suggestion
        else:
            user_action = "check API keys and model configuration"

            # Available alternatives
        alternatives_text = ""
        if available_models:
            alternatives_text = f" Available models: {', '.join(available_models)}"

        # Capitalize only the first letter if it's lowercase, preserve the rest
        if user_action and user_action[0].islower():
            user_action = user_action[0].upper() + user_action[1:]

        return f"{what_failed}: {why_failed}. {user_action}.{alternatives_text}"

    @staticmethod
    def format_file_error(operation: str, file_path: str, reason: str, solution: str | None = None) -> str:
        """Format a file operation error message.

        Args:
            operation: The file operation that failed (e.g., "read", "write", "delete")
            file_path: Path to the file
            reason: Why the operation failed
            solution: Suggested solution

        Returns:
            Formatted error message following Dana standard

        Example:
            >>> ErrorFormattingUtilities.format_file_error(
            ...     operation="read",
            ...     file_path="/path/to/config.json",
            ...     reason="file not found",
            ...     solution="create the configuration file"
            ... )
            "File read failed: file not found at '/path/to/config.json'. Create the configuration file. Check file path and permissions"
        """
        # What failed
        what_failed = f"File {operation} failed"

        # Why it failed
        why_failed = f"{reason} at '{file_path}'"

        # What user can do
        if solution:
            user_action = solution
        else:
            user_action = "check file path and try again"

            # Available alternatives
        alternatives_text = " Check file path and permissions"

        # Capitalize only the first letter if it's lowercase, preserve the rest
        if user_action and user_action[0].islower():
            user_action = user_action[0].upper() + user_action[1:]

        return f"{what_failed}: {why_failed}. {user_action}.{alternatives_text}"

    @staticmethod
    def format_generic_error(
        operation: str, reason: str, suggestion: str | None = None, context: str = "", alternatives: list[str] | None = None
    ) -> str:
        """Format a generic error message following Dana standards.

        Args:
            operation: The operation that failed
            reason: Why the operation failed
            suggestion: Suggested solution
            context: Optional context information
            alternatives: List of alternative approaches

        Returns:
            Formatted error message following Dana standard

        Example:
            >>> ErrorFormattingUtilities.format_generic_error(
            ...     operation="data processing",
            ...     reason="invalid input format",
            ...     suggestion="ensure input follows expected schema",
            ...     alternatives=["use data converter", "provide sample data"]
            ... )
            "Data processing failed: invalid input format. Ensure input follows expected schema. Available alternatives: use data converter, provide sample data"
        """
        context_suffix = f" in {context}" if context else ""

        # What failed
        what_failed = f"{operation.capitalize()} failed"

        # Why it failed
        why_failed = f"{reason}{context_suffix}"

        # What user can do
        if suggestion:
            user_action = suggestion
        else:
            user_action = "check parameters and try again"

            # Available alternatives
        alternatives_text = ""
        if alternatives:
            alternatives_text = f" Available alternatives: {', '.join(alternatives)}"

        # Capitalize only the first letter if it's lowercase, preserve the rest
        if user_action and user_action[0].islower():
            user_action = user_action[0].upper() + user_action[1:]

        return f"{what_failed}: {why_failed}. {user_action}.{alternatives_text}"

    @staticmethod
    def log_formatted_error(error_message: str, logger_method: str = "error", extra_context: dict[str, Any] | None = None) -> None:
        """Log a formatted error message using DANA_LOGGER.

        Args:
            error_message: The formatted error message
            logger_method: Logger method to use ("error", "warning", "info")
            extra_context: Additional context to include in log

        Example:
            >>> ErrorFormattingUtilities.log_formatted_error(
            ...     error_message="Resource 'database' unavailable: connection timeout",
            ...     logger_method="error",
            ...     extra_context={"resource_type": "database", "operation": "connect"}
            ... )
        """
        # Use getattr with default None, fallback to error if not callable
        logger_func = getattr(DANA_LOGGER, logger_method, None)
        if not callable(logger_func):
            logger_func = DANA_LOGGER.error

        if extra_context:
            logger_func(error_message, extra=extra_context)
        else:
            logger_func(error_message)
