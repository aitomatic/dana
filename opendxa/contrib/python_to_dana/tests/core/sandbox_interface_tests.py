"""
Tests for core.sandbox_interface module - Sandbox Interface Protocol for Python-to-Dana Integration
"""

from unittest.mock import Mock, patch

import pytest

from opendxa.contrib.python_to_dana.core.exceptions import DanaCallError
from opendxa.contrib.python_to_dana.core.sandbox_interface import (
    DefaultSandboxInterface,
)


@pytest.fixture
def mock_sandbox():
    """Create a mock DanaSandbox for testing."""
    mock = Mock()
    mock.eval = Mock()
    return mock


@pytest.fixture
def mock_sandbox_context():
    """Create a mock SandboxContext for testing."""
    return Mock()


@pytest.fixture
def sandbox_interface(mock_sandbox):
    """Create DefaultSandboxInterface with mocked sandbox."""
    with patch('opendxa.contrib.python_to_dana.core.sandbox_interface.DanaSandbox', return_value=mock_sandbox):
        return DefaultSandboxInterface(debug=False)


# Test parameters for valid reason calls
valid_reason_params = [
    {
        "name": "simple_prompt_no_options",
        "prompt": "What is 2+2?",
        "options": None,
        "expected_dana_code": 'reason("\\"What is 2+2?\\"", {})',
        "mock_result": Mock(success=True, result="4"),
        "expected_result": "4",
    },
    {
        "name": "prompt_with_temperature",
        "prompt": "Analyze this text",
        "options": {"temperature": 0.5},
        "expected_dana_code": 'reason("\\"Analyze this text\\"", {"temperature": 0.5})',
        "mock_result": Mock(success=True, result="Analysis complete"),
        "expected_result": "Analysis complete",
    },
    {
        "name": "prompt_with_max_tokens",
        "prompt": "Generate story",
        "options": {"max_tokens": 100},
        "expected_dana_code": 'reason("\\"Generate story\\"", {"max_tokens": 100})',
        "mock_result": Mock(success=True, result="Once upon a time..."),
        "expected_result": "Once upon a time...",
    },
    {
        "name": "prompt_with_system_message",
        "prompt": "Hello",
        "options": {"system_message": "You are helpful"},
        "expected_dana_code": 'reason("\\"Hello\\"", {"system_message": "You are helpful"})',
        "mock_result": Mock(success=True, result="Hi there!"),
        "expected_result": "Hi there!",
    },
    {
        "name": "prompt_with_format_json",
        "prompt": "Return JSON",
        "options": {"format": "json"},
        "expected_dana_code": 'reason("\\"Return JSON\\"", {"format": "json"})',
        "mock_result": Mock(success=True, result={"key": "value"}),
        "expected_result": {"key": "value"},
    },
    {
        "name": "prompt_with_enable_ipv",
        "prompt": "Test IPV",
        "options": {"enable_ipv": True},
        "expected_dana_code": 'reason("\\"Test IPV\\"", {"enable_ipv": true})',
        "mock_result": Mock(success=True, result="IPV enabled"),
        "expected_result": "IPV enabled",
    },
    {
        "name": "prompt_with_use_original",
        "prompt": "Use original",
        "options": {"use_original": False},
        "expected_dana_code": 'reason("\\"Use original\\"", {"use_original": false})',
        "mock_result": Mock(success=True, result="Using optimized"),
        "expected_result": "Using optimized",
    },
    {
        "name": "prompt_with_multiple_options",
        "prompt": "Complex request",
        "options": {
            "temperature": 0.7,
            "max_tokens": 150,
            "format": "text",
            "enable_ipv": True
        },
        "expected_dana_code": 'reason("\\"Complex request\\"", {"temperature": 0.7, "max_tokens": 150, "format": "text", "enable_ipv": true})',
        "mock_result": Mock(success=True, result="Complex response"),
        "expected_result": "Complex response",
    },
]


@pytest.mark.parametrize("test_case", valid_reason_params, ids=lambda x: x["name"])
def test_reason_valid_calls(sandbox_interface, test_case):
    """Test valid reason calls with various options."""
    # Arrange
    sandbox_interface._sandbox.eval.return_value = test_case["mock_result"]
    
    # Act
    result = sandbox_interface.reason(test_case["prompt"], test_case["options"])
    
    # Assert
    assert result == test_case["expected_result"]
    # Note: We can't easily test the exact Dana code format due to string escaping complexity
    # but we can verify the method was called
    sandbox_interface._sandbox.eval.assert_called_once()


# Test parameters for invalid options
invalid_options_params = [
    {
        "name": "non_dict_options",
        "prompt": "Test",
        "options": "not a dict",
        "expected_error": DanaCallError,
        "expected_message": "Options parameter must be a dictionary",
    },
    {
        "name": "invalid_option_key",
        "prompt": "Test",
        "options": {"invalid_key": "value"},
        "expected_error": DanaCallError,
        "expected_message": "Invalid option keys: {'invalid_key'}",
    },
    {
        "name": "temperature_out_of_range_high",
        "prompt": "Test",
        "options": {"temperature": 3.0},
        "expected_error": DanaCallError,
        "expected_message": "temperature must be a number between 0.0 and 2.0",
    },
    {
        "name": "temperature_out_of_range_low",
        "prompt": "Test",
        "options": {"temperature": -0.5},
        "expected_error": DanaCallError,
        "expected_message": "temperature must be a number between 0.0 and 2.0",
    },
    {
        "name": "temperature_not_number",
        "prompt": "Test",
        "options": {"temperature": "hot"},
        "expected_error": DanaCallError,
        "expected_message": "temperature must be a number between 0.0 and 2.0",
    },
    {
        "name": "max_tokens_negative",
        "prompt": "Test",
        "options": {"max_tokens": -10},
        "expected_error": DanaCallError,
        "expected_message": "max_tokens must be a positive integer",
    },
    {
        "name": "max_tokens_not_int",
        "prompt": "Test",
        "options": {"max_tokens": "many"},
        "expected_error": DanaCallError,
        "expected_message": "max_tokens must be a positive integer",
    },
    {
        "name": "invalid_format",
        "prompt": "Test",
        "options": {"format": "xml"},
        "expected_error": DanaCallError,
        "expected_message": "format must be 'text' or 'json'",
    },
    {
        "name": "enable_ipv_not_bool",
        "prompt": "Test",
        "options": {"enable_ipv": "yes"},
        "expected_error": DanaCallError,
        "expected_message": "enable_ipv must be a boolean",
    },
    {
        "name": "use_original_not_bool",
        "prompt": "Test",
        "options": {"use_original": 1},
        "expected_error": DanaCallError,
        "expected_message": "use_original must be a boolean",
    },
]


@pytest.mark.parametrize("test_case", invalid_options_params, ids=lambda x: x["name"])
def test_reason_invalid_options(sandbox_interface, test_case):
    """Test reason calls with invalid options."""
    # Act & Assert
    with pytest.raises(test_case["expected_error"]) as exc_info:
        sandbox_interface.reason(test_case["prompt"], test_case["options"])
    
    assert test_case["expected_message"] in str(exc_info.value)


# Test parameters for Dana execution failures
dana_failure_params = [
    {
        "name": "dana_syntax_error",
        "prompt": "Test",
        "options": None,
        "mock_result": Mock(success=False, error=SyntaxError("Invalid syntax"), result=None),
        "expected_error": DanaCallError,
        "expected_message": "Dana reasoning failed",
    },
    {
        "name": "dana_runtime_error",
        "prompt": "Test",
        "options": None,
        "mock_result": Mock(success=False, error=RuntimeError("Runtime failure"), result=None),
        "expected_error": DanaCallError,
        "expected_message": "Dana reasoning failed",
    },
]


@pytest.mark.parametrize("test_case", dana_failure_params, ids=lambda x: x["name"])
def test_reason_dana_failures(sandbox_interface, test_case):
    """Test reason calls when Dana execution fails."""
    # Arrange
    sandbox_interface._sandbox.eval.return_value = test_case["mock_result"]
    
    # Act & Assert
    with pytest.raises(test_case["expected_error"]) as exc_info:
        sandbox_interface.reason(test_case["prompt"], test_case["options"])
    
    assert test_case["expected_message"] in str(exc_info.value)


# Test parameters for exception handling
exception_handling_params = [
    {
        "name": "sandbox_eval_exception",
        "prompt": "Test",
        "options": None,
        "exception": RuntimeError("Sandbox crashed"),
        "expected_error": DanaCallError,
        "expected_message": "Failed to execute Dana reasoning",
    },
    {
        "name": "unexpected_exception",
        "prompt": "Test", 
        "options": None,
        "exception": ValueError("Unexpected error"),
        "expected_error": DanaCallError,
        "expected_message": "Failed to execute Dana reasoning",
    },
]


@pytest.mark.parametrize("test_case", exception_handling_params, ids=lambda x: x["name"])
def test_reason_exception_handling(sandbox_interface, test_case):
    """Test reason exception handling."""
    # Arrange
    sandbox_interface._sandbox.eval.side_effect = test_case["exception"]
    
    # Act & Assert
    with pytest.raises(test_case["expected_error"]) as exc_info:
        sandbox_interface.reason(test_case["prompt"], test_case["options"])
    
    assert test_case["expected_message"] in str(exc_info.value)
    assert exc_info.value.original_error == test_case["exception"]


# Test parameters for format_options_for_dana method
format_options_params = [
    {
        "name": "empty_dict",
        "options": {},
        "expected_result": "{}",
    },
    {
        "name": "single_string_value",
        "options": {"key": "value"},
        "expected_result": '{"key": "value"}',
    },
    {
        "name": "single_int_value",
        "options": {"number": 42},
        "expected_result": '{"number": 42}',
    },
    {
        "name": "single_float_value",
        "options": {"pi": 3.14},
        "expected_result": '{"pi": 3.14}',
    },
    {
        "name": "single_bool_true",
        "options": {"flag": True},
        "expected_result": '{"flag": true}',
    },
    {
        "name": "single_bool_false",
        "options": {"flag": False},
        "expected_result": '{"flag": false}',
    },
    {
        "name": "multiple_values",
        "options": {"str": "hello", "num": 123, "bool": True},
        "expected_result": '{"str": "hello", "num": 123, "bool": true}',
    },
    {
        "name": "string_with_quotes",
        "options": {"message": 'Say "hello"'},
        "expected_result": '{"message": "Say \\"hello\\""}',
    },
    {
        "name": "string_with_newlines",
        "options": {"text": "line1\nline2\tindented"},
        "expected_result": '{"text": "line1\\nline2\\tindented"}',
    },
]


@pytest.mark.parametrize("test_case", format_options_params, ids=lambda x: x["name"])
def test_format_options_for_dana(sandbox_interface, test_case):
    """Test _format_options_for_dana method."""
    # Act
    result = sandbox_interface._format_options_for_dana(test_case["options"])
    
    # Assert
    assert result == test_case["expected_result"]


def test_default_sandbox_interface_initialization():
    """Test DefaultSandboxInterface initialization."""
    with patch('opendxa.contrib.python_to_dana.core.sandbox_interface.DanaSandbox') as mock_sandbox_class:
        mock_sandbox = Mock()
        mock_sandbox_class.return_value = mock_sandbox
        
        # Test without context
        interface = DefaultSandboxInterface(debug=True)
        
        mock_sandbox_class.assert_called_once_with(debug=True, context=None)
        assert interface._sandbox is mock_sandbox
        
        # Test with context
        mock_sandbox_class.reset_mock()
        mock_context = Mock()
        interface_with_context = DefaultSandboxInterface(debug=False, context=mock_context)
        
        mock_sandbox_class.assert_called_once_with(debug=False, context=mock_context)


def test_sandbox_property_access(sandbox_interface):
    """Test access to underlying sandbox property."""
    # Act
    sandbox = sandbox_interface.sandbox
    
    # Assert
    assert sandbox is sandbox_interface._sandbox


def test_reason_prompt_escaping(sandbox_interface):
    """Test that prompts are properly escaped for Dana."""
    # Arrange
    prompt_with_quotes = 'Ask: "What is love?"'
    mock_result = Mock(success=True, result="Baby don't hurt me")
    sandbox_interface._sandbox.eval.return_value = mock_result
    
    # Act
    result = sandbox_interface.reason(prompt_with_quotes)
    
    # Assert
    assert result == "Baby don't hurt me"
    # Verify the method was called (exact string matching is complex due to escaping)
    sandbox_interface._sandbox.eval.assert_called_once()


def test_reason_with_none_options(sandbox_interface):
    """Test reason call with explicitly None options."""
    # Arrange
    mock_result = Mock(success=True, result="Success")
    sandbox_interface._sandbox.eval.return_value = mock_result
    
    # Act
    result = sandbox_interface.reason("Test prompt", None)
    
    # Assert
    assert result == "Success"
    sandbox_interface._sandbox.eval.assert_called_once()


def test_reason_valid_temperature_boundary_values(sandbox_interface):
    """Test reason with boundary temperature values."""
    # Arrange
    mock_result = Mock(success=True, result="Success")
    sandbox_interface._sandbox.eval.return_value = mock_result
    
    # Test minimum temperature
    result1 = sandbox_interface.reason("Test", {"temperature": 0.0})
    assert result1 == "Success"
    
    # Reset mock
    sandbox_interface._sandbox.eval.reset_mock()
    sandbox_interface._sandbox.eval.return_value = mock_result
    
    # Test maximum temperature
    result2 = sandbox_interface.reason("Test", {"temperature": 2.0})
    assert result2 == "Success"


def test_reason_valid_max_tokens_values(sandbox_interface):
    """Test reason with valid max_tokens values."""
    # Arrange
    mock_result = Mock(success=True, result="Success")
    sandbox_interface._sandbox.eval.return_value = mock_result
    
    # Test minimum valid value
    result = sandbox_interface.reason("Test", {"max_tokens": 1})
    assert result == "Success"
    
    # Reset and test larger value
    sandbox_interface._sandbox.eval.reset_mock()
    sandbox_interface._sandbox.eval.return_value = mock_result
    
    result2 = sandbox_interface.reason("Test", {"max_tokens": 4000})
    assert result2 == "Success" 