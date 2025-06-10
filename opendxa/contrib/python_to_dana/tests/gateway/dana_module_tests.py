"""
Tests for gateway.dana_module module - Main Dana Module Implementation for Python-to-Dana Integration
"""

from unittest.mock import Mock, patch

import pytest

from opendxa.contrib.python_to_dana.core.exceptions import DanaCallError
from opendxa.contrib.python_to_dana.gateway.dana_module import Dana


@pytest.fixture
def mock_sandbox_interface():
    """Create a mock sandbox interface for testing."""
    mock = Mock()
    mock.reason = Mock()
    return mock


@pytest.fixture
def dana_module(mock_sandbox_interface):
    """Create Dana module with mocked sandbox interface."""
    with patch('opendxa.contrib.python_to_dana.gateway.dana_module.DefaultSandboxInterface', return_value=mock_sandbox_interface):
        return Dana(debug=False)


@pytest.fixture
def dana_module_debug(mock_sandbox_interface):
    """Create Dana module in debug mode with mocked sandbox interface."""
    with patch('opendxa.contrib.python_to_dana.gateway.dana_module.DefaultSandboxInterface', return_value=mock_sandbox_interface):
        return Dana(debug=True)


# Test parameters for valid reason calls
valid_reason_calls_params = [
    {
        "name": "simple_string_prompt",
        "prompt": "What is 2+2?",
        "options": None,
        "mock_return": "The answer is 4",
        "expected_result": "The answer is 4",
    },
    {
        "name": "prompt_with_temperature_option",
        "prompt": "Tell me a story",
        "options": {"temperature": 0.7},
        "mock_return": "Once upon a time...",
        "expected_result": "Once upon a time...",
    },
    {
        "name": "prompt_with_multiple_options",
        "prompt": "Analyze data",
        "options": {"temperature": 0.5, "max_tokens": 100, "format": "json"},
        "mock_return": {"analysis": "complete"},
        "expected_result": {"analysis": "complete"},
    },
    {
        "name": "complex_prompt_text",
        "prompt": "Given the following data:\n1. Item A: $100\n2. Item B: $200\nCalculate the total",
        "options": {"format": "text"},
        "mock_return": "Total: $300",
        "expected_result": "Total: $300",
    },
    {
        "name": "empty_options_dict",
        "prompt": "Simple question",
        "options": {},
        "mock_return": "Simple answer",
        "expected_result": "Simple answer",
    },
]


@pytest.mark.parametrize("test_case", valid_reason_calls_params, ids=lambda x: x["name"])
def test_reason_valid_calls(dana_module, test_case):
    """Test valid reason calls with various inputs."""
    # Arrange
    dana_module._sandbox_interface.reason.return_value = test_case["mock_return"]
    
    # Act
    result = dana_module.reason(test_case["prompt"], test_case["options"])
    
    # Assert
    assert result == test_case["expected_result"]
    dana_module._sandbox_interface.reason.assert_called_once_with(test_case["prompt"], test_case["options"])


# Test parameters for invalid type inputs
invalid_type_params = [
    {
        "name": "non_string_prompt_int",
        "prompt": 123,
        "options": None,
        "expected_error": TypeError,
        "expected_message": "Expected str, got int at argument 'prompt'",
    },
    {
        "name": "non_string_prompt_list",
        "prompt": ["question", "parts"],
        "options": None,
        "expected_error": TypeError,
        "expected_message": "Expected str, got list at argument 'prompt'",
    },
    {
        "name": "non_string_prompt_none",
        "prompt": None,
        "options": None,
        "expected_error": TypeError,
        "expected_message": "Expected str, got NoneType at argument 'prompt'",
    },
    {
        "name": "non_dict_options_string",
        "prompt": "Valid prompt",
        "options": "invalid options",
        "expected_error": TypeError,
        "expected_message": "Expected dict, got str at argument 'options'",
    },
    {
        "name": "non_dict_options_list",
        "prompt": "Valid prompt",
        "options": ["option1", "option2"],
        "expected_error": TypeError,
        "expected_message": "Expected dict, got list at argument 'options'",
    },
    {
        "name": "non_dict_options_int",
        "prompt": "Valid prompt",
        "options": 42,
        "expected_error": TypeError,
        "expected_message": "Expected dict, got int at argument 'options'",
    },
]


@pytest.mark.parametrize("test_case", invalid_type_params, ids=lambda x: x["name"])
def test_reason_invalid_types(dana_module, test_case):
    """Test reason calls with invalid input types."""
    # Act & Assert
    with pytest.raises(test_case["expected_error"]) as exc_info:
        dana_module.reason(test_case["prompt"], test_case["options"])
    
    assert test_case["expected_message"] in str(exc_info.value)
    # Sandbox should not be called for type validation errors
    dana_module._sandbox_interface.reason.assert_not_called()


# Test parameters for sandbox interface errors
sandbox_error_params = [
    {
        "name": "dana_call_error",
        "prompt": "Test prompt",
        "options": None,
        "sandbox_exception": DanaCallError("Dana execution failed"),
        "expected_error": DanaCallError,
        "expected_message": "Dana execution failed",
    },
    {
        "name": "type_error_from_sandbox",
        "prompt": "Test prompt",
        "options": None,
        "sandbox_exception": TypeError("Type error in sandbox"),
        "expected_error": TypeError,
        "expected_message": "Type error in sandbox",
    },
    {
        "name": "generic_exception",
        "prompt": "Test prompt",
        "options": None,
        "sandbox_exception": RuntimeError("Unexpected runtime error"),
        "expected_error": DanaCallError,
        "expected_message": "Unexpected error in reasoning",
    },
    {
        "name": "value_error",
        "prompt": "Test prompt",
        "options": None,
        "sandbox_exception": ValueError("Invalid value"),
        "expected_error": DanaCallError,
        "expected_message": "Unexpected error in reasoning",
    },
]


@pytest.mark.parametrize("test_case", sandbox_error_params, ids=lambda x: x["name"])
def test_reason_sandbox_errors(dana_module, test_case):
    """Test reason calls when sandbox interface raises errors."""
    # Arrange
    dana_module._sandbox_interface.reason.side_effect = test_case["sandbox_exception"]
    
    # Act & Assert
    with pytest.raises(test_case["expected_error"]) as exc_info:
        dana_module.reason(test_case["prompt"], test_case["options"])
    
    assert test_case["expected_message"] in str(exc_info.value)
    dana_module._sandbox_interface.reason.assert_called_once_with(test_case["prompt"], test_case["options"])


# Test parameters for debug mode functionality
debug_mode_params = [
    {
        "name": "simple_call_debug",
        "prompt": "Debug test",
        "options": None,
        "mock_return": "Debug result",
    },
    {
        "name": "call_with_options_debug",
        "prompt": "Debug with options",
        "options": {"temperature": 0.5},
        "mock_return": "Debug result with options",
    },
]


@pytest.mark.parametrize("test_case", debug_mode_params, ids=lambda x: x["name"])
def test_reason_debug_mode(dana_module_debug, test_case, capsys):
    """Test reason calls in debug mode produce appropriate debug output."""
    # Arrange
    dana_module_debug._sandbox_interface.reason.return_value = test_case["mock_return"]
    # Reset call count for isolated test
    dana_module_debug._call_count = 0
    
    # Act
    result = dana_module_debug.reason(test_case["prompt"], test_case["options"])
    
    # Assert
    assert result == test_case["mock_return"]
    
    # Check debug output
    captured = capsys.readouterr()
    assert "DEBUG: Dana call #1" in captured.out
    assert "succeeded" in captured.out


def test_reason_debug_mode_error(dana_module_debug, capsys):
    """Test debug output when errors occur."""
    # Arrange
    error = DanaCallError("Test error")
    dana_module_debug._sandbox_interface.reason.side_effect = error
    
    # Act & Assert
    with pytest.raises(DanaCallError):
        dana_module_debug.reason("Test prompt", None)
    
    # Check debug output
    captured = capsys.readouterr()
    assert "DEBUG: Call #1 failed" in captured.out
    assert "DanaCallError" in captured.out


def test_dana_initialization():
    """Test Dana module initialization."""
    with patch('opendxa.contrib.python_to_dana.gateway.dana_module.DefaultSandboxInterface') as mock_interface_class:
        mock_interface = Mock()
        mock_interface_class.return_value = mock_interface
        
        # Test normal mode
        dana = Dana(debug=False)
        
        mock_interface_class.assert_called_once_with(debug=False)
        assert dana._sandbox_interface is mock_interface
        assert dana._debug is False
        assert dana._call_count == 0
        
        # Test debug mode
        mock_interface_class.reset_mock()
        dana_debug = Dana(debug=True)
        
        mock_interface_class.assert_called_once_with(debug=True)
        assert dana_debug._debug is True


def test_debug_property(dana_module, dana_module_debug):
    """Test debug property access."""
    assert dana_module.debug is False
    assert dana_module_debug.debug is True


def test_sandbox_property(dana_module):
    """Test sandbox property access."""
    assert dana_module.sandbox is dana_module._sandbox_interface


def test_dana_repr(dana_module, dana_module_debug):
    """Test string representation of Dana module."""
    # Test normal mode
    repr_normal = repr(dana_module)
    assert "Dana(mode=normal, calls=0)" == repr_normal
    
    # Test debug mode
    repr_debug = repr(dana_module_debug)
    assert "Dana(mode=debug, calls=0)" == repr_debug
    
    # Test after some calls
    dana_module._call_count = 5
    repr_with_calls = repr(dana_module)
    assert "Dana(mode=normal, calls=5)" == repr_with_calls


def test_call_count_increment(dana_module):
    """Test that call count increments properly."""
    # Arrange
    dana_module._sandbox_interface.reason.return_value = "result"
    
    # Initial count should be 0
    assert dana_module._call_count == 0
    
    # Make first call
    dana_module.reason("First prompt", None)
    assert dana_module._call_count == 1
    
    # Make second call
    dana_module.reason("Second prompt", None)
    assert dana_module._call_count == 2
    
    # Make call with options
    dana_module.reason("Third prompt", {"temperature": 0.5})
    assert dana_module._call_count == 3


def test_reason_with_various_option_combinations(dana_module):
    """Test reason with different valid option combinations."""
    # Arrange
    dana_module._sandbox_interface.reason.return_value = "success"
    
    test_options = [
        {"temperature": 0.5},
        {"max_tokens": 100},
        {"format": "json"},
        {"system_message": "Be helpful"},
        {"enable_ipv": True},
        {"use_original": False},
        {
            "temperature": 0.7,
            "max_tokens": 200,
            "format": "text",
            "system_message": "Custom system",
            "enable_ipv": False,
            "use_original": True
        }
    ]
    
    for i, options in enumerate(test_options, 1):
        # Act
        result = dana_module.reason(f"Test prompt {i}", options)
        
        # Assert
        assert result == "success"
        assert dana_module._call_count == i


def test_reason_preserves_exception_types(dana_module):
    """Test that specific exception types are preserved correctly."""
    # Test TypeError preservation
    dana_module._sandbox_interface.reason.side_effect = TypeError("Type error")
    with pytest.raises(TypeError) as exc_info:
        dana_module.reason("test", None)
    assert "Type error" in str(exc_info.value)
    
    # Reset and test DanaCallError preservation
    dana_module._sandbox_interface.reason.side_effect = DanaCallError("Dana error")
    with pytest.raises(DanaCallError) as exc_info:
        dana_module.reason("test", None)
    assert "Dana error" in str(exc_info.value)


def test_reason_long_prompt_debug_truncation(dana_module_debug, capsys):
    """Test that long prompts are truncated in debug output."""
    # Arrange
    long_prompt = "This is a very long prompt that should be truncated in debug output " * 10
    dana_module_debug._sandbox_interface.reason.return_value = "result"
    
    # Act
    dana_module_debug.reason(long_prompt, None)
    
    # Assert
    captured = capsys.readouterr()
    # Should contain truncated version with "..."
    assert "..." in captured.out
    # Should not contain the full long prompt
    assert len(long_prompt) > 50
    debug_line = [line for line in captured.out.split('\n') if 'DEBUG: Dana call' in line][0]
    assert len(debug_line) < len(long_prompt)


def test_reason_none_options_handling(dana_module):
    """Test explicit None options handling."""
    # Arrange
    dana_module._sandbox_interface.reason.return_value = "success"
    
    # Act
    result = dana_module.reason("Test prompt", None)
    
    # Assert
    assert result == "success"
    dana_module._sandbox_interface.reason.assert_called_once_with("Test prompt", None) 