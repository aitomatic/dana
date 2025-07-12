"""
Tests for core.types module - Type System for Python-to-Dana Integration
"""

import pytest

from dana.integrations.python.to_dana.core.types import (
    DANA_TO_PYTHON_TYPES,
    PYTHON_TO_DANA_TYPES,
    DanaType,
    format_type_error,
    get_dana_type,
    validate_python_type,
)

# Test parameters for DanaType enum
dana_type_values_params = [
    {
        "name": "int_type",
        "type_value": DanaType.INT,
        "expected_value": "int",
    },
    {
        "name": "float_type",
        "type_value": DanaType.FLOAT,
        "expected_value": "float",
    },
    {
        "name": "string_type",
        "type_value": DanaType.STRING,
        "expected_value": "string",
    },
    {
        "name": "bool_type",
        "type_value": DanaType.BOOL,
        "expected_value": "bool",
    },
    {
        "name": "list_type",
        "type_value": DanaType.LIST,
        "expected_value": "list",
    },
    {
        "name": "dict_type",
        "type_value": DanaType.DICT,
        "expected_value": "dict",
    },
    {
        "name": "tuple_type",
        "type_value": DanaType.TUPLE,
        "expected_value": "tuple",
    },
    {
        "name": "set_type",
        "type_value": DanaType.SET,
        "expected_value": "set",
    },
    {
        "name": "null_type",
        "type_value": DanaType.NULL,
        "expected_value": "null",
    },
    {
        "name": "any_type",
        "type_value": DanaType.ANY,
        "expected_value": "any",
    },
]


@pytest.mark.parametrize("test_case", dana_type_values_params, ids=lambda x: x["name"])
def test_dana_type_values(test_case):
    """Test that DanaType enum values are correct."""
    # Act
    result = test_case["type_value"].value

    # Assert
    assert result == test_case["expected_value"]


# Test parameters for get_dana_type function
get_dana_type_params = [
    {
        "name": "string_value",
        "python_value": "hello",
        "expected_type": DanaType.STRING,
    },
    {
        "name": "int_value",
        "python_value": 42,
        "expected_type": DanaType.INT,
    },
    {
        "name": "float_value",
        "python_value": 3.14,
        "expected_type": DanaType.FLOAT,
    },
    {
        "name": "bool_true_value",
        "python_value": True,
        "expected_type": DanaType.BOOL,
    },
    {
        "name": "bool_false_value",
        "python_value": False,
        "expected_type": DanaType.BOOL,
    },
    {
        "name": "list_value",
        "python_value": [1, 2, 3],
        "expected_type": DanaType.LIST,
    },
    {
        "name": "dict_value",
        "python_value": {"key": "value"},
        "expected_type": DanaType.DICT,
    },
    {
        "name": "tuple_value",
        "python_value": (1, 2, 3),
        "expected_type": DanaType.TUPLE,
    },
    {
        "name": "set_value",
        "python_value": {1, 2, 3},
        "expected_type": DanaType.SET,
    },
    {
        "name": "none_value",
        "python_value": None,
        "expected_type": DanaType.NULL,
    },
    {
        "name": "custom_object",
        "python_value": object(),
        "expected_type": DanaType.ANY,
    },
]


@pytest.mark.parametrize("test_case", get_dana_type_params, ids=lambda x: x["name"])
def test_get_dana_type(test_case):
    """Test get_dana_type function with various Python values."""
    # Act
    result = get_dana_type(test_case["python_value"])

    # Assert
    assert result == test_case["expected_type"]


# Test parameters for validate_python_type function
validate_python_type_params = [
    {
        "name": "valid_string",
        "value": "hello",
        "expected_type": str,
        "expected_result": True,
    },
    {
        "name": "valid_int",
        "value": 42,
        "expected_type": int,
        "expected_result": True,
    },
    {
        "name": "valid_float",
        "value": 3.14,
        "expected_type": float,
        "expected_result": True,
    },
    {
        "name": "valid_bool",
        "value": True,
        "expected_type": bool,
        "expected_result": True,
    },
    {
        "name": "valid_list",
        "value": [1, 2, 3],
        "expected_type": list,
        "expected_result": True,
    },
    {
        "name": "valid_dict",
        "value": {"key": "value"},
        "expected_type": dict,
        "expected_result": True,
    },
    {
        "name": "invalid_string_as_int",
        "value": "hello",
        "expected_type": int,
        "expected_result": False,
    },
    {
        "name": "invalid_int_as_string",
        "value": 42,
        "expected_type": str,
        "expected_result": False,
    },
    {
        "name": "invalid_list_as_dict",
        "value": [1, 2, 3],
        "expected_type": dict,
        "expected_result": False,
    },
]


@pytest.mark.parametrize("test_case", validate_python_type_params, ids=lambda x: x["name"])
def test_validate_python_type(test_case):
    """Test validate_python_type function with various values and types."""
    # Act
    result = validate_python_type(test_case["value"], test_case["expected_type"])

    # Assert
    assert result == test_case["expected_result"]


# Test parameters for format_type_error function
format_type_error_params = [
    {
        "name": "string_expected_int_no_context",
        "value": "hello",
        "expected_type": int,
        "context": "",
        "expected_message": "Expected int, got str",
    },
    {
        "name": "int_expected_string_with_context",
        "value": 42,
        "expected_type": str,
        "context": "function argument",
        "expected_message": "Expected str, got int at function argument",
    },
    {
        "name": "list_expected_dict_no_context",
        "value": [1, 2, 3],
        "expected_type": dict,
        "context": "",
        "expected_message": "Expected dict, got list",
    },
    {
        "name": "none_expected_string_with_context",
        "value": None,
        "expected_type": str,
        "context": "parameter 'name'",
        "expected_message": "Expected str, got NoneType at parameter 'name'",
    },
]


@pytest.mark.parametrize("test_case", format_type_error_params, ids=lambda x: x["name"])
def test_format_type_error(test_case):
    """Test format_type_error function with various values and contexts."""
    # Act
    result = format_type_error(test_case["value"], test_case["expected_type"], test_case["context"])

    # Assert
    assert result == test_case["expected_message"]


def test_python_to_dana_types_mapping():
    """Test that PYTHON_TO_DANA_TYPES mapping is complete and correct."""
    expected_mappings = {
        str: DanaType.STRING,
        int: DanaType.INT,
        float: DanaType.FLOAT,
        bool: DanaType.BOOL,
        list: DanaType.LIST,
        dict: DanaType.DICT,
        tuple: DanaType.TUPLE,
        set: DanaType.SET,
        type(None): DanaType.NULL,
    }

    assert PYTHON_TO_DANA_TYPES == expected_mappings


def test_dana_to_python_types_mapping():
    """Test that DANA_TO_PYTHON_TYPES is the reverse of PYTHON_TO_DANA_TYPES."""
    # Check that it's the reverse mapping
    for python_type, dana_type in PYTHON_TO_DANA_TYPES.items():
        assert DANA_TO_PYTHON_TYPES[dana_type] == python_type

    # Check that all Dana types are represented
    assert len(DANA_TO_PYTHON_TYPES) == len(PYTHON_TO_DANA_TYPES)
