"""
Tests for In-Process Sandbox Interface

Tests the InProcessSandboxInterface implementation to ensure it properly
executes Dana code in-process while maintaining sandbox boundaries.
"""

from unittest.mock import Mock, patch

import pytest

from dana.integrations.python.to_dana.core.exceptions import DanaCallError
from dana.integrations.python.to_dana.core.inprocess_sandbox import InProcessSandboxInterface

# Table-driven test parameters for option formatting
format_options_params = [
    {
        "name": "empty_dict",
        "input_options": {},
        "expected_output": "{}",
    },
    {
        "name": "string_value",
        "input_options": {"model": "gpt-4"},
        "expected_contains": ['"model": "gpt-4"'],
        "starts_with": "{",
        "ends_with": "}",
    },
    {
        "name": "boolean_true",
        "input_options": {"enable_ipv": True},
        "expected_contains": ['"enable_ipv": true'],
        "starts_with": "{",
        "ends_with": "}",
    },
    {
        "name": "boolean_false",
        "input_options": {"enable_ipv": False},
        "expected_contains": ['"enable_ipv": false'],
        "starts_with": "{",
        "ends_with": "}",
    },
    {
        "name": "integer_value",
        "input_options": {"max_tokens": 100},
        "expected_contains": ['"max_tokens": 100'],
        "starts_with": "{",
        "ends_with": "}",
    },
    {
        "name": "float_value",
        "input_options": {"temperature": 0.7},
        "expected_contains": ['"temperature": 0.7'],
        "starts_with": "{",
        "ends_with": "}",
    },
    {
        "name": "complex_options",
        "input_options": {"system_message": "Be helpful", "temperature": 0.5, "enable_ipv": False, "max_tokens": 100},
        "expected_contains": ['"system_message": "Be helpful"', '"temperature": 0.5', '"enable_ipv": false', '"max_tokens": 100'],
        "starts_with": "{",
        "ends_with": "}",
    },
]

# Table-driven test parameters for temperature validation
temperature_validation_params = [
    {
        "name": "valid_temperature_0_0",
        "temperature": 0.0,
        "should_raise": False,
    },
    {
        "name": "valid_temperature_0_5",
        "temperature": 0.5,
        "should_raise": False,
    },
    {
        "name": "valid_temperature_1_0",
        "temperature": 1.0,
        "should_raise": False,
    },
    {
        "name": "valid_temperature_1_5",
        "temperature": 1.5,
        "should_raise": False,
    },
    {
        "name": "valid_temperature_2_0",
        "temperature": 2.0,
        "should_raise": False,
    },
    {
        "name": "invalid_temperature_negative",
        "temperature": -0.1,
        "should_raise": True,
        "error_message": "temperature must be a number between 0.0 and 2.0",
    },
    {
        "name": "invalid_temperature_too_high",
        "temperature": 2.1,
        "should_raise": True,
        "error_message": "temperature must be a number between 0.0 and 2.0",
    },
    {
        "name": "invalid_temperature_way_too_high",
        "temperature": 3.0,
        "should_raise": True,
        "error_message": "temperature must be a number between 0.0 and 2.0",
    },
    {
        "name": "invalid_temperature_string",
        "temperature": "hot",
        "should_raise": True,
        "error_message": "temperature must be a number between 0.0 and 2.0",
    },
    {
        "name": "invalid_temperature_none",
        "temperature": None,
        "should_raise": True,
        "error_message": "temperature must be a number between 0.0 and 2.0",
    },
]

# Table-driven test parameters for max_tokens validation
max_tokens_validation_params = [
    {
        "name": "valid_max_tokens_1",
        "max_tokens": 1,
        "should_raise": False,
    },
    {
        "name": "valid_max_tokens_10",
        "max_tokens": 10,
        "should_raise": False,
    },
    {
        "name": "valid_max_tokens_100",
        "max_tokens": 100,
        "should_raise": False,
    },
    {
        "name": "valid_max_tokens_1000",
        "max_tokens": 1000,
        "should_raise": False,
    },
    {
        "name": "invalid_max_tokens_zero",
        "max_tokens": 0,
        "should_raise": True,
        "error_message": "max_tokens must be a positive integer",
    },
    {
        "name": "invalid_max_tokens_negative",
        "max_tokens": -1,
        "should_raise": True,
        "error_message": "max_tokens must be a positive integer",
    },
    {
        "name": "invalid_max_tokens_float",
        "max_tokens": 0.5,
        "should_raise": True,
        "error_message": "max_tokens must be a positive integer",
    },
    {
        "name": "invalid_max_tokens_string",
        "max_tokens": "many",
        "should_raise": True,
        "error_message": "max_tokens must be a positive integer",
    },
    {
        "name": "invalid_max_tokens_none",
        "max_tokens": None,
        "should_raise": True,
        "error_message": "max_tokens must be a positive integer",
    },
]

# Table-driven test parameters for format validation
format_validation_params = [
    {
        "name": "valid_format_text",
        "format_value": "text",
        "should_raise": False,
    },
    {
        "name": "valid_format_json",
        "format_value": "json",
        "should_raise": False,
    },
    {
        "name": "invalid_format_xml",
        "format_value": "xml",
        "should_raise": True,
        "error_message": "format must be 'text' or 'json'",
    },
    {
        "name": "invalid_format_yaml",
        "format_value": "yaml",
        "should_raise": True,
        "error_message": "format must be 'text' or 'json'",
    },
    {
        "name": "invalid_format_integer",
        "format_value": 123,
        "should_raise": True,
        "error_message": "format must be 'text' or 'json'",
    },
    {
        "name": "invalid_format_none",
        "format_value": None,
        "should_raise": True,
        "error_message": "format must be 'text' or 'json'",
    },
]

# Table-driven test parameters for boolean options validation
boolean_options_validation_params = [
    {
        "name": "enable_ipv_string_true",
        "option_name": "enable_ipv",
        "option_value": "true",
        "should_raise": True,
        "error_message": "enable_ipv must be a boolean",
    },
    {
        "name": "enable_ipv_string_false",
        "option_name": "enable_ipv",
        "option_value": "false",
        "should_raise": True,
        "error_message": "enable_ipv must be a boolean",
    },
    {
        "name": "enable_ipv_integer_1",
        "option_name": "enable_ipv",
        "option_value": 1,
        "should_raise": True,
        "error_message": "enable_ipv must be a boolean",
    },
    {
        "name": "enable_ipv_integer_0",
        "option_name": "enable_ipv",
        "option_value": 0,
        "should_raise": True,
        "error_message": "enable_ipv must be a boolean",
    },
    {
        "name": "enable_ipv_none",
        "option_name": "enable_ipv",
        "option_value": None,
        "should_raise": True,
        "error_message": "enable_ipv must be a boolean",
    },
    {
        "name": "use_original_string_true",
        "option_name": "use_original",
        "option_value": "true",
        "should_raise": True,
        "error_message": "use_original must be a boolean",
    },
    {
        "name": "use_original_integer_1",
        "option_name": "use_original",
        "option_value": 1,
        "should_raise": True,
        "error_message": "use_original must be a boolean",
    },
]

# Table-driven test parameters for invalid option keys
invalid_option_keys_params = [
    {
        "name": "single_invalid_key",
        "options": {"invalid_key": "value"},
        "should_raise": True,
        "error_message": "Invalid option keys",
    },
    {
        "name": "mixed_valid_invalid_keys",
        "options": {"temperature": 0.5, "invalid_key": "value"},
        "should_raise": True,
        "error_message": "Invalid option keys",
    },
    {
        "name": "completely_wrong_option",
        "options": {"completely_wrong": "option"},
        "should_raise": True,
        "error_message": "Invalid option keys",
    },
]

# Table-driven test parameters for non-dict options
non_dict_options_params = [
    {
        "name": "string_options",
        "options": "string",
        "should_raise": True,
        "error_message": "Options parameter must be a dictionary",
    },
    {
        "name": "integer_options",
        "options": 123,
        "should_raise": True,
        "error_message": "Options parameter must be a dictionary",
    },
    {
        "name": "list_options",
        "options": [],
        "should_raise": True,
        "error_message": "Options parameter must be a dictionary",
    },
]


class TestInProcessSandboxInterface:
    """Test the InProcessSandboxInterface implementation."""

    def test_initialization(self):
        """Test that InProcessSandboxInterface initializes correctly."""
        sandbox = InProcessSandboxInterface(debug=True)

        assert sandbox._debug is True
        assert sandbox._context is None
        assert sandbox._sandbox is not None

    def test_initialization_with_context(self):
        """Test initialization with custom context."""
        from dana.core.lang.sandbox_context import SandboxContext

        context = SandboxContext()
        sandbox = InProcessSandboxInterface(debug=False, context=context)

        assert sandbox._debug is False
        assert sandbox._context is context
        assert sandbox._sandbox is not None

    @pytest.mark.parametrize("test_case", format_options_params, ids=lambda x: x["name"])
    def test_format_options_for_dana(self, test_case):
        """Test _format_options_for_dana with various inputs."""
        sandbox = InProcessSandboxInterface()
        result = sandbox._format_options_for_dana(test_case["input_options"])

        if "expected_output" in test_case:
            assert result == test_case["expected_output"]

        if "expected_contains" in test_case:
            for expected_string in test_case["expected_contains"]:
                assert expected_string in result

        if "starts_with" in test_case:
            assert result.startswith(test_case["starts_with"])

        if "ends_with" in test_case:
            assert result.endswith(test_case["ends_with"])

    @pytest.mark.parametrize("test_case", temperature_validation_params, ids=lambda x: x["name"])
    @patch("dana.integrations.python.to_dana.core.inprocess_sandbox.DanaSandbox")
    def test_option_validation_temperature(self, mock_dana_sandbox, test_case):
        """Test option validation for temperature values."""
        # Setup mock
        mock_sandbox_instance = Mock()
        mock_dana_sandbox.return_value = mock_sandbox_instance

        mock_result = Mock()
        mock_result.success = True
        mock_result.result = "mocked response"
        mock_sandbox_instance.execute_string.return_value = mock_result

        sandbox = InProcessSandboxInterface()

        if test_case["should_raise"]:
            with pytest.raises(DanaCallError, match=test_case["error_message"]):
                sandbox.reason("test", {"temperature": test_case["temperature"]})
        else:
            # Should not raise validation errors during option validation
            result = sandbox.reason("test", {"temperature": test_case["temperature"]})
            assert result == "mocked response"
            # Verify the sandbox.execute_string was called with proper Dana code
            mock_sandbox_instance.execute_string.assert_called_once()

    @pytest.mark.parametrize("test_case", max_tokens_validation_params, ids=lambda x: x["name"])
    @patch("dana.integrations.python.to_dana.core.inprocess_sandbox.DanaSandbox")
    def test_option_validation_max_tokens(self, mock_dana_sandbox, test_case):
        """Test option validation for max_tokens values."""
        # Setup mock
        mock_sandbox_instance = Mock()
        mock_dana_sandbox.return_value = mock_sandbox_instance

        mock_result = Mock()
        mock_result.success = True
        mock_result.result = "mocked response"
        mock_sandbox_instance.execute_string.return_value = mock_result

        sandbox = InProcessSandboxInterface()

        if test_case["should_raise"]:
            with pytest.raises(DanaCallError, match=test_case["error_message"]):
                sandbox.reason("test", {"max_tokens": test_case["max_tokens"]})
        else:
            result = sandbox.reason("test", {"max_tokens": test_case["max_tokens"]})
            assert result == "mocked response"
            mock_sandbox_instance.execute_string.assert_called_once()

    @pytest.mark.parametrize("test_case", format_validation_params, ids=lambda x: x["name"])
    @patch("dana.integrations.python.to_dana.core.inprocess_sandbox.DanaSandbox")
    def test_option_validation_format(self, mock_dana_sandbox, test_case):
        """Test option validation for format values."""
        # Setup mock
        mock_sandbox_instance = Mock()
        mock_dana_sandbox.return_value = mock_sandbox_instance

        mock_result = Mock()
        mock_result.success = True
        mock_result.result = "mocked response"
        mock_sandbox_instance.execute_string.return_value = mock_result

        sandbox = InProcessSandboxInterface()

        if test_case["should_raise"]:
            with pytest.raises(DanaCallError, match=test_case["error_message"]):
                sandbox.reason("test", {"format": test_case["format_value"]})
        else:
            result = sandbox.reason("test", {"format": test_case["format_value"]})
            assert result == "mocked response"
            mock_sandbox_instance.execute_string.assert_called_once()

    @pytest.mark.parametrize("test_case", boolean_options_validation_params, ids=lambda x: x["name"])
    def test_option_validation_boolean_options(self, test_case):
        """Test option validation for boolean options."""
        sandbox = InProcessSandboxInterface()

        # These should fail validation before reaching sandbox.execute_string
        with pytest.raises(DanaCallError, match=test_case["error_message"]):
            sandbox.reason("test", {test_case["option_name"]: test_case["option_value"]})

    @pytest.mark.parametrize("test_case", invalid_option_keys_params, ids=lambda x: x["name"])
    def test_option_validation_invalid_keys(self, test_case):
        """Test option validation for invalid option keys."""
        sandbox = InProcessSandboxInterface()

        # These should fail validation before reaching sandbox.execute_string
        with pytest.raises(DanaCallError, match=test_case["error_message"]):
            sandbox.reason("test", test_case["options"])

    @pytest.mark.parametrize("test_case", non_dict_options_params, ids=lambda x: x["name"])
    def test_option_validation_non_dict_options(self, test_case):
        """Test option validation when options is not a dict."""
        sandbox = InProcessSandboxInterface()

        # These should fail validation before reaching sandbox.execute_string
        with pytest.raises(DanaCallError, match=test_case["error_message"]):
            sandbox.reason("test", test_case["options"])

    @patch("dana.integrations.python.to_dana.core.inprocess_sandbox.DanaSandbox")
    def test_successful_reason_call(self, mock_dana_sandbox):
        """Test successful reason call with mocked sandbox."""
        # Setup mock
        mock_sandbox_instance = Mock()
        mock_dana_sandbox.return_value = mock_sandbox_instance

        mock_result = Mock()
        mock_result.success = True
        mock_result.result = "Successful mocked response"
        mock_sandbox_instance.execute_string.return_value = mock_result

        sandbox = InProcessSandboxInterface()
        result = sandbox.reason("What is 2+2?", {"temperature": 0.5})

        # Verify response
        assert result == "Successful mocked response"

        # Verify the Dana code was properly constructed and called
        mock_sandbox_instance.execute_string.assert_called_once()
        call_args = mock_sandbox_instance.execute_string.call_args[0]
        dana_code = call_args[0]

        # Should contain the prompt and formatted options
        assert "What is 2+2?" in dana_code
        assert '"temperature": 0.5' in dana_code

    @patch("dana.integrations.python.to_dana.core.inprocess_sandbox.DanaSandbox")
    def test_sandbox_execution_failure(self, mock_dana_sandbox):
        """Test handling of sandbox execution failures."""
        # Setup mock for failure case
        mock_sandbox_instance = Mock()
        mock_dana_sandbox.return_value = mock_sandbox_instance

        mock_result = Mock()
        mock_result.success = False
        mock_result.error = "Mocked execution error"
        mock_sandbox_instance.execute_string.return_value = mock_result

        sandbox = InProcessSandboxInterface()

        with pytest.raises(DanaCallError, match="Dana reasoning failed"):
            sandbox.reason("Test prompt", {"temperature": 0.5})

    def test_close_method(self):
        """Test that close method works without errors."""
        sandbox = InProcessSandboxInterface()
        sandbox.close()  # Should not raise any exceptions

    def test_close_method_debug_output(self, capsys):
        """Test close method debug output."""
        sandbox = InProcessSandboxInterface(debug=True)
        sandbox.close()

        captured = capsys.readouterr()
        assert "DEBUG: InProcessSandboxInterface closing" in captured.out

    def test_sandbox_property_access(self):
        """Test access to underlying sandbox property."""
        sandbox = InProcessSandboxInterface()

        # Should provide access to underlying DanaSandbox
        assert hasattr(sandbox, "sandbox")
        underlying_sandbox = sandbox.sandbox
        assert underlying_sandbox is not None

        # Should be the actual DanaSandbox instance
        from dana.core.lang.dana_sandbox import DanaSandbox

        assert isinstance(underlying_sandbox, DanaSandbox)

    def test_thread_safety_isolation(self):
        """Test that different instances have isolated state."""
        sandbox1 = InProcessSandboxInterface(debug=True)
        sandbox2 = InProcessSandboxInterface(debug=False)

        # Should have separate sandbox instances
        assert sandbox1._sandbox is not sandbox2._sandbox
        assert sandbox1._debug != sandbox2._debug

    @patch("dana.integrations.python.to_dana.core.inprocess_sandbox.DanaSandbox")
    def test_debug_mode_logging(self, mock_dana_sandbox, capsys):
        """Test debug mode logging output."""
        # Setup mock
        mock_sandbox_instance = Mock()
        mock_dana_sandbox.return_value = mock_sandbox_instance

        mock_result = Mock()
        mock_result.success = True
        mock_result.result = "test response"
        mock_sandbox_instance.execute_string.return_value = mock_result

        # Test with debug enabled
        sandbox = InProcessSandboxInterface(debug=True)
        sandbox.reason("test prompt")

        captured = capsys.readouterr()
        assert "DEBUG: InProcessSandboxInterface executing Dana code" in captured.out


class TestInProcessSandboxInterfaceIntegration:
    """Integration tests for InProcessSandboxInterface."""

    def test_interface_compliance(self):
        """Test that InProcessSandboxInterface follows the expected interface."""
        sandbox = InProcessSandboxInterface()

        # Should have all required methods
        assert hasattr(sandbox, "reason")
        assert hasattr(sandbox, "close")
        assert callable(sandbox.reason)
        assert callable(sandbox.close)

    def test_can_be_used_polymorphically(self):
        """Test that it can be used polymorphically with other sandbox implementations."""
        sandbox = InProcessSandboxInterface()

        # Should be usable in functions expecting SandboxInterface
        def use_sandbox(s):
            assert hasattr(s, "reason")
            assert hasattr(s, "close")
            s.close()
            return True

        assert use_sandbox(sandbox) is True
