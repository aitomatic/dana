"""
Tests for core.exceptions module - Exception classes for Python-to-Dana Integration
"""

import pytest

from dana.integrations.python.to_dana.core.exceptions import (
    DanaCallError,
    DanaError,
    ResourceError,
    SecurityError,
    TypeConversionError,
)

# Test parameters for DanaError base exception
dana_error_params = [
    {
        "name": "simple_message",
        "message": "Something went wrong",
        "expected_message": "Something went wrong",
    },
    {
        "name": "empty_message",
        "message": "",
        "expected_message": "",
    },
    {
        "name": "complex_message",
        "message": "Error in module X: Failed to process data",
        "expected_message": "Error in module X: Failed to process data",
    },
]


@pytest.mark.parametrize("test_case", dana_error_params, ids=lambda x: x["name"])
def test_dana_error_creation(test_case):
    """Test DanaError exception creation and message handling."""
    # Act
    error = DanaError(test_case["message"])

    # Assert
    assert str(error) == test_case["expected_message"]
    assert isinstance(error, Exception)
    assert isinstance(error, DanaError)


# Test parameters for DanaCallError exception
dana_call_error_params = [
    {
        "name": "message_only",
        "message": "Dana call failed",
        "original_error": None,
        "expected_message": "Dana call failed",
        "expected_original": None,
    },
    {
        "name": "message_with_original_error",
        "message": "Dana reasoning failed",
        "original_error": ValueError("Invalid input"),
        "expected_message": "Dana reasoning failed",
        "expected_original": ValueError,
    },
    {
        "name": "message_with_runtime_error",
        "message": "Execution failed",
        "original_error": RuntimeError("Process crashed"),
        "expected_message": "Execution failed",
        "expected_original": RuntimeError,
    },
]


@pytest.mark.parametrize("test_case", dana_call_error_params, ids=lambda x: x["name"])
def test_dana_call_error_creation(test_case):
    """Test DanaCallError exception creation with optional original error."""
    # Act
    error = DanaCallError(test_case["message"], test_case["original_error"])

    # Assert
    assert str(error) == test_case["expected_message"]
    assert isinstance(error, DanaError)
    assert isinstance(error, DanaCallError)

    if test_case["expected_original"] is None:
        assert error.original_error is None
    else:
        assert isinstance(error.original_error, test_case["expected_original"])


# Test parameters for TypeConversionError exception
type_conversion_error_params = [
    {
        "name": "message_only",
        "message": "Type conversion failed",
        "python_type": None,
        "dana_type": None,
        "expected_message": "Type conversion failed",
        "expected_python_type": None,
        "expected_dana_type": None,
    },
    {
        "name": "message_with_python_type",
        "message": "Cannot convert list to Dana",
        "python_type": list,
        "dana_type": None,
        "expected_message": "Cannot convert list to Dana",
        "expected_python_type": list,
        "expected_dana_type": None,
    },
    {
        "name": "message_with_dana_type",
        "message": "Invalid Dana type",
        "python_type": None,
        "dana_type": "invalid_type",
        "expected_message": "Invalid Dana type",
        "expected_python_type": None,
        "expected_dana_type": "invalid_type",
    },
    {
        "name": "message_with_both_types",
        "message": "Type mismatch",
        "python_type": str,
        "dana_type": "int",
        "expected_message": "Type mismatch",
        "expected_python_type": str,
        "expected_dana_type": "int",
    },
]


@pytest.mark.parametrize("test_case", type_conversion_error_params, ids=lambda x: x["name"])
def test_type_conversion_error_creation(test_case):
    """Test TypeConversionError exception creation with type information."""
    # Act
    error = TypeConversionError(test_case["message"], test_case["python_type"], test_case["dana_type"])

    # Assert
    assert str(error) == test_case["expected_message"]
    assert isinstance(error, DanaError)
    assert isinstance(error, TypeConversionError)
    assert error.python_type == test_case["expected_python_type"]
    assert error.dana_type == test_case["expected_dana_type"]


# Test parameters for ResourceError exception
resource_error_params = [
    {
        "name": "llm_connection_error",
        "message": "Failed to connect to LLM service",
        "expected_message": "Failed to connect to LLM service",
    },
    {
        "name": "memory_limit_error",
        "message": "Memory limit exceeded",
        "expected_message": "Memory limit exceeded",
    },
    {
        "name": "timeout_error",
        "message": "Request timeout",
        "expected_message": "Request timeout",
    },
]


@pytest.mark.parametrize("test_case", resource_error_params, ids=lambda x: x["name"])
def test_resource_error_creation(test_case):
    """Test ResourceError exception creation."""
    # Act
    error = ResourceError(test_case["message"])

    # Assert
    assert str(error) == test_case["expected_message"]
    assert isinstance(error, DanaError)
    assert isinstance(error, ResourceError)


# Test parameters for SecurityError exception
security_error_params = [
    {
        "name": "sandbox_breach",
        "message": "Sandbox security boundary violated",
        "expected_message": "Sandbox security boundary violated",
    },
    {
        "name": "unauthorized_access",
        "message": "Unauthorized access to protected resource",
        "expected_message": "Unauthorized access to protected resource",
    },
    {
        "name": "malicious_code",
        "message": "Malicious code detected",
        "expected_message": "Malicious code detected",
    },
]


@pytest.mark.parametrize("test_case", security_error_params, ids=lambda x: x["name"])
def test_security_error_creation(test_case):
    """Test SecurityError exception creation."""
    # Act
    error = SecurityError(test_case["message"])

    # Assert
    assert str(error) == test_case["expected_message"]
    assert isinstance(error, DanaError)
    assert isinstance(error, SecurityError)


def test_exception_inheritance_hierarchy():
    """Test that all custom exceptions inherit properly from DanaError."""
    # All custom exceptions should inherit from DanaError
    exceptions_to_test = [
        DanaCallError("test"),
        TypeConversionError("test"),
        ResourceError("test"),
        SecurityError("test"),
    ]

    for error in exceptions_to_test:
        assert isinstance(error, DanaError)
        assert isinstance(error, Exception)


def test_dana_call_error_with_chained_exceptions():
    """Test DanaCallError properly handles exception chaining."""
    # Arrange
    original_error = ValueError("Original problem")

    # Act
    dana_error = DanaCallError("Wrapper error", original_error)

    # Assert
    assert dana_error.original_error is original_error
    assert isinstance(dana_error.original_error, ValueError)
    assert str(dana_error.original_error) == "Original problem"


def test_type_conversion_error_type_tracking():
    """Test TypeConversionError properly tracks type information."""
    # Arrange
    python_type = dict
    dana_type = "list"

    # Act
    error = TypeConversionError("Type mismatch", python_type, dana_type)

    # Assert
    assert error.python_type is python_type
    assert error.dana_type == dana_type

    # Test with None values
    error_no_types = TypeConversionError("Generic error")
    assert error_no_types.python_type is None
    assert error_no_types.dana_type is None
