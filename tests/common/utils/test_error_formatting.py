"""Test suite for ErrorFormattingUtilities.

This module tests the error formatting utilities to ensure they produce
consistent, standardized error messages following the OpenDXA format:
"[What failed]: [Why it failed]. [What user can do]. [Available alternatives]"
"""

import pytest
from unittest.mock import patch

from opendxa.common.utils.error_formatting import ErrorFormattingUtilities


class TestErrorFormattingUtilities:
    """Test class for ErrorFormattingUtilities methods."""

    def test_format_resource_error_basic(self):
        """Test basic resource error formatting."""
        result = ErrorFormattingUtilities.format_resource_error(resource_name="database", reason="connection timeout")

        expected = "Resource 'database' unavailable: connection timeout. Check resource configuration and try again."
        assert result == expected

    def test_format_resource_error_with_action(self):
        """Test resource error formatting with custom action."""
        result = ErrorFormattingUtilities.format_resource_error(
            resource_name="llm_model", reason="API key not found", action="set OPENAI_API_KEY environment variable"
        )

        expected = "Resource 'llm_model' unavailable: API key not found. Set OPENAI_API_KEY environment variable."
        assert result == expected

    def test_format_resource_error_with_alternatives(self):
        """Test resource error formatting with alternatives."""
        result = ErrorFormattingUtilities.format_resource_error(
            resource_name="storage",
            reason="disk full",
            action="free up disk space",
            alternatives=["use backup storage", "compress existing files"],
        )

        expected = "Resource 'storage' unavailable: disk full. Free up disk space. Available alternatives: use backup storage, compress existing files"
        assert result == expected

    def test_format_resource_error_with_context(self):
        """Test resource error formatting with context."""
        result = ErrorFormattingUtilities.format_resource_error(
            resource_name="cache", reason="memory exhausted", context="during initialization"
        )

        expected = "Resource 'cache' unavailable: memory exhausted in during initialization. Check resource configuration and try again."
        assert result == expected

    def test_format_validation_error_basic(self):
        """Test basic validation error formatting."""
        result = ErrorFormattingUtilities.format_validation_error(field_name="temperature", value=150, reason="value exceeds maximum")

        expected = "Field 'temperature' validation failed: value exceeds maximum (got 150). Check field requirements and provide valid value. Check field requirements and valid ranges"
        assert result == expected

    def test_format_validation_error_with_expected(self):
        """Test validation error formatting with expected value."""
        result = ErrorFormattingUtilities.format_validation_error(
            field_name="port", value=-1, reason="must be positive", expected="value between 1 and 65535"
        )

        expected = "Field 'port' validation failed: must be positive (got -1). Provide value between 1 and 65535. Check field requirements and valid ranges"
        assert result == expected

    def test_format_validation_error_with_context(self):
        """Test validation error formatting with context."""
        result = ErrorFormattingUtilities.format_validation_error(
            field_name="config_key", value="invalid@key", reason="contains invalid characters", context="configuration file"
        )

        expected = "Field 'config_key' validation failed: contains invalid characters (got invalid@key) in configuration file. Check field requirements and provide valid value. Check field requirements and valid ranges"
        assert result == expected

    def test_format_configuration_error_basic(self):
        """Test basic configuration error formatting."""
        result = ErrorFormattingUtilities.format_configuration_error(config_key="database.host", issue="missing required value")

        expected = "Configuration 'database.host' invalid: missing required value. Check configuration format and provide valid value. Check configuration file format and required keys"
        assert result == expected

    def test_format_configuration_error_with_solution(self):
        """Test configuration error formatting with solution."""
        result = ErrorFormattingUtilities.format_configuration_error(
            config_key="llm.model", issue="not found in configuration", solution="add model configuration to config file"
        )

        expected = "Configuration 'llm.model' invalid: not found in configuration. Add model configuration to config file. Check configuration file format and required keys"
        assert result == expected

    def test_format_configuration_error_with_config_file(self):
        """Test configuration error formatting with config file."""
        result = ErrorFormattingUtilities.format_configuration_error(
            config_key="api.key", issue="invalid format", solution="provide valid API key", config_file="opendxa_config.json"
        )

        expected = "Configuration 'api.key' invalid: invalid format 'opendxa_config.json'. Provide valid API key. Check configuration file format and required keys"
        assert result == expected

    def test_format_llm_error_basic(self):
        """Test basic LLM error formatting."""
        result = ErrorFormattingUtilities.format_llm_error(operation="query processing", reason="model not available")

        expected = "LLM query processing failed: model not available. Check API keys and model configuration."
        assert result == expected

    def test_format_llm_error_with_model(self):
        """Test LLM error formatting with model name."""
        result = ErrorFormattingUtilities.format_llm_error(
            operation="initialization", reason="API key not found", model_name="gpt-4", suggestion="set OPENAI_API_KEY environment variable"
        )

        expected = "LLM initialization failed: API key not found for model 'gpt-4'. Set OPENAI_API_KEY environment variable."
        assert result == expected

    def test_format_llm_error_with_available_models(self):
        """Test LLM error formatting with available models."""
        result = ErrorFormattingUtilities.format_llm_error(
            operation="model selection", reason="requested model unavailable", available_models=["gpt-3.5-turbo", "claude-3-sonnet"]
        )

        expected = "LLM model selection failed: requested model unavailable. Check API keys and model configuration. Available models: gpt-3.5-turbo, claude-3-sonnet"
        assert result == expected

    def test_format_file_error_basic(self):
        """Test basic file error formatting."""
        result = ErrorFormattingUtilities.format_file_error(operation="read", file_path="/path/to/file.txt", reason="file not found")

        expected = "File read failed: file not found at '/path/to/file.txt'. Check file path and try again. Check file path and permissions"
        assert result == expected

    def test_format_file_error_with_solution(self):
        """Test file error formatting with solution."""
        result = ErrorFormattingUtilities.format_file_error(
            operation="write", file_path="/tmp/output.json", reason="permission denied", solution="ensure directory is writable"
        )

        expected = (
            "File write failed: permission denied at '/tmp/output.json'. Ensure directory is writable. Check file path and permissions"
        )
        assert result == expected

    def test_format_generic_error_basic(self):
        """Test basic generic error formatting."""
        result = ErrorFormattingUtilities.format_generic_error(operation="data processing", reason="invalid input format")

        expected = "Data processing failed: invalid input format. Check parameters and try again."
        assert result == expected

    def test_format_generic_error_with_alternatives(self):
        """Test generic error formatting with alternatives."""
        result = ErrorFormattingUtilities.format_generic_error(
            operation="network connection",
            reason="timeout occurred",
            suggestion="increase timeout duration",
            alternatives=["use different endpoint", "retry with exponential backoff"],
        )

        expected = "Network connection failed: timeout occurred. Increase timeout duration. Available alternatives: use different endpoint, retry with exponential backoff"
        assert result == expected

    def test_format_generic_error_with_context(self):
        """Test generic error formatting with context."""
        result = ErrorFormattingUtilities.format_generic_error(
            operation="authentication", reason="invalid credentials", context="user login"
        )

        expected = "Authentication failed: invalid credentials in user login. Check parameters and try again."
        assert result == expected

    def test_log_formatted_error_basic(self):
        """Test logging of formatted error message."""
        with patch("opendxa.common.utils.error_formatting.DXA_LOGGER") as mock_logger:
            ErrorFormattingUtilities.log_formatted_error(error_message="Test error message")

            mock_logger.error.assert_called_once_with("Test error message")

    def test_log_formatted_error_with_method(self):
        """Test logging with different logger method."""
        with patch("opendxa.common.utils.error_formatting.DXA_LOGGER") as mock_logger:
            ErrorFormattingUtilities.log_formatted_error(error_message="Warning message", logger_method="warning")

            mock_logger.warning.assert_called_once_with("Warning message")

    def test_log_formatted_error_with_context(self):
        """Test logging with extra context."""
        with patch("opendxa.common.utils.error_formatting.DXA_LOGGER") as mock_logger:
            extra_context = {"operation": "test", "user_id": "123"}
            ErrorFormattingUtilities.log_formatted_error(error_message="Error with context", extra_context=extra_context)

            mock_logger.error.assert_called_once_with("Error with context", extra=extra_context)

    def test_log_formatted_error_invalid_method(self):
        """Test logging with invalid logger method falls back to error."""
        with patch("opendxa.common.utils.error_formatting.DXA_LOGGER") as mock_logger:
            ErrorFormattingUtilities.log_formatted_error(error_message="Test message", logger_method="invalid_method")

            # Should fall back to error method
            mock_logger.error.assert_called_once_with("Test message")

    def test_error_message_format_consistency(self):
        """Test that all error messages follow the standard format."""
        # Test resource error
        resource_error = ErrorFormattingUtilities.format_resource_error(resource_name="test", reason="test reason", action="test action")
        assert ": " in resource_error and ". " in resource_error

        # Test validation error
        validation_error = ErrorFormattingUtilities.format_validation_error(field_name="test", value="test", reason="test reason")
        assert ": " in validation_error and ". " in validation_error

        # Test configuration error
        config_error = ErrorFormattingUtilities.format_configuration_error(config_key="test", issue="test issue")
        assert ": " in config_error and ". " in config_error

        # Test LLM error
        llm_error = ErrorFormattingUtilities.format_llm_error(operation="test", reason="test reason")
        assert ": " in llm_error and ". " in llm_error

        # Test file error
        file_error = ErrorFormattingUtilities.format_file_error(operation="test", file_path="/test", reason="test reason")
        assert ": " in file_error and ". " in file_error

        # Test generic error
        generic_error = ErrorFormattingUtilities.format_generic_error(operation="test", reason="test reason")
        assert ": " in generic_error and ". " in generic_error

    def test_empty_alternatives_handling(self):
        """Test handling of empty alternatives list."""
        result = ErrorFormattingUtilities.format_resource_error(resource_name="test", reason="test reason", alternatives=[])

        assert "Available alternatives:" not in result

    def test_none_alternatives_handling(self):
        """Test handling of None alternatives."""
        result = ErrorFormattingUtilities.format_generic_error(operation="test", reason="test reason", alternatives=None)

        assert "Available alternatives:" not in result

    def test_capitalization_consistency(self):
        """Test that user actions are properly capitalized."""
        result = ErrorFormattingUtilities.format_resource_error(
            resource_name="test", reason="test reason", action="check configuration and retry"
        )

        # Should capitalize the first letter of the action
        assert ". Check configuration and retry." in result
