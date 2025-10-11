"""
Tests for utils.converter module - Type Conversion Utilities for Python-to-Dana Integration
"""

import pytest

from dana.integrations.python.to_dana.core.exceptions import TypeConversionError
from dana.integrations.python.to_dana.core.types import DanaType
from dana.integrations.python.to_dana.utils.converter import (
    BasicTypeConverter,
    validate_and_convert,
)

# Test parameters for BasicTypeConverter.to_dana method
to_dana_params = [
    {
        "name": "string_value",
        "input_value": "hello world",
        "expected_type": DanaType.STRING,
        "expected_value": "hello world",
    },
    {
        "name": "int_value",
        "input_value": 42,
        "expected_type": DanaType.INT,
        "expected_value": 42,
    },
    {
        "name": "float_value",
        "input_value": 3.14,
        "expected_type": DanaType.FLOAT,
        "expected_value": 3.14,
    },
    {
        "name": "bool_true_value",
        "input_value": True,
        "expected_type": DanaType.BOOL,
        "expected_value": True,
    },
    {
        "name": "bool_false_value",
        "input_value": False,
        "expected_type": DanaType.BOOL,
        "expected_value": False,
    },
    {
        "name": "none_value",
        "input_value": None,
        "expected_type": DanaType.NULL,
        "expected_value": None,
    },
    {
        "name": "empty_list",
        "input_value": [],
        "expected_type": DanaType.LIST,
        "expected_value": [],
    },
    {
        "name": "simple_list",
        "input_value": [1, 2, 3],
        "expected_type": DanaType.LIST,
        "expected_value": [1, 2, 3],
    },
    {
        "name": "mixed_list",
        "input_value": [1, "hello", True, None],
        "expected_type": DanaType.LIST,
        "expected_value": [1, "hello", True, None],
    },
    {
        "name": "empty_dict",
        "input_value": {},
        "expected_type": DanaType.DICT,
        "expected_value": {},
    },
    {
        "name": "simple_dict",
        "input_value": {"key": "value", "number": 42},
        "expected_type": DanaType.DICT,
        "expected_value": {"key": "value", "number": 42},
    },
    {
        "name": "tuple_to_list",
        "input_value": (1, 2, 3),
        "expected_type": DanaType.LIST,
        "expected_value": [1, 2, 3],
    },
    {
        "name": "set_to_list",
        "input_value": {1, 2, 3},
        "expected_type": DanaType.LIST,
        "expected_value": [1, 2, 3],  # Note: order may vary, tested separately
    },
]


@pytest.mark.parametrize("test_case", to_dana_params, ids=lambda x: x["name"])
def test_basic_type_converter_to_dana(test_case):
    """Test BasicTypeConverter.to_dana with various Python types."""
    # Arrange
    converter = BasicTypeConverter()

    # Act
    result_type, result_value = converter.to_dana(test_case["input_value"])

    # Assert
    assert result_type == test_case["expected_type"]

    # Special handling for sets since order isn't guaranteed
    if test_case["name"] == "set_to_list":
        assert set(result_value) == set(test_case["expected_value"])
    else:
        assert result_value == test_case["expected_value"]


# Test parameters for nested data structures
nested_data_params = [
    {
        "name": "nested_list",
        "input_value": [[1, 2], [3, 4]],
        "expected_type": DanaType.LIST,
        "expected_value": [[1, 2], [3, 4]],
    },
    {
        "name": "nested_dict",
        "input_value": {"outer": {"inner": "value"}},
        "expected_type": DanaType.DICT,
        "expected_value": {"outer": {"inner": "value"}},
    },
    {
        "name": "list_with_dict",
        "input_value": [{"key": "value"}, {"number": 42}],
        "expected_type": DanaType.LIST,
        "expected_value": [{"key": "value"}, {"number": 42}],
    },
    {
        "name": "dict_with_list",
        "input_value": {"numbers": [1, 2, 3], "words": ["a", "b"]},
        "expected_type": DanaType.DICT,
        "expected_value": {"numbers": [1, 2, 3], "words": ["a", "b"]},
    },
]


@pytest.mark.parametrize("test_case", nested_data_params, ids=lambda x: x["name"])
def test_basic_type_converter_to_dana_nested(test_case):
    """Test BasicTypeConverter.to_dana with nested data structures."""
    # Arrange
    converter = BasicTypeConverter()

    # Act
    result_type, result_value = converter.to_dana(test_case["input_value"])

    # Assert
    assert result_type == test_case["expected_type"]
    assert result_value == test_case["expected_value"]


# Test parameters for BasicTypeConverter.from_dana method
from_dana_params = [
    {
        "name": "string_value",
        "dana_type": DanaType.STRING,
        "input_value": "hello world",
        "expected_value": "hello world",
    },
    {
        "name": "int_value",
        "dana_type": DanaType.INT,
        "input_value": 42,
        "expected_value": 42,
    },
    {
        "name": "float_value",
        "dana_type": DanaType.FLOAT,
        "input_value": 3.14,
        "expected_value": 3.14,
    },
    {
        "name": "bool_value",
        "dana_type": DanaType.BOOL,
        "input_value": True,
        "expected_value": True,
    },
    {
        "name": "null_value",
        "dana_type": DanaType.NULL,
        "input_value": None,
        "expected_value": None,
    },
    {
        "name": "list_value",
        "dana_type": DanaType.LIST,
        "input_value": [1, 2, 3],
        "expected_value": [1, 2, 3],
    },
    {
        "name": "dict_value",
        "dana_type": DanaType.DICT,
        "input_value": {"key": "value"},
        "expected_value": {"key": "value"},
    },
]


@pytest.mark.parametrize("test_case", from_dana_params, ids=lambda x: x["name"])
def test_basic_type_converter_from_dana(test_case):
    """Test BasicTypeConverter.from_dana with various Dana types."""
    # Arrange
    converter = BasicTypeConverter()

    # Act
    result = converter.from_dana(test_case["dana_type"], test_case["input_value"])

    # Assert
    assert result == test_case["expected_value"]


# Test parameters for error cases in to_dana
to_dana_error_params = [
    {
        "name": "dict_with_non_string_key",
        "input_value": {42: "value"},
        "expected_error": TypeConversionError,
        "expected_message_contains": "Dictionary keys must be strings",
    },
]


@pytest.mark.parametrize("test_case", to_dana_error_params, ids=lambda x: x["name"])
def test_basic_type_converter_to_dana_errors(test_case):
    """Test BasicTypeConverter.to_dana error handling."""
    # Arrange
    converter = BasicTypeConverter()

    # Act & Assert
    with pytest.raises(test_case["expected_error"]) as exc_info:
        converter.to_dana(test_case["input_value"])

    assert test_case["expected_message_contains"] in str(exc_info.value)


# Test parameters for error cases in from_dana
from_dana_error_params = [
    {
        "name": "invalid_list_type",
        "dana_type": DanaType.LIST,
        "input_value": "not a list",
        "expected_error": TypeConversionError,
        "expected_message_contains": "Expected list for Dana list",
    },
    {
        "name": "invalid_dict_type",
        "dana_type": DanaType.DICT,
        "input_value": "not a dict",
        "expected_error": TypeConversionError,
        "expected_message_contains": "Expected dict for Dana dict",
    },
]


@pytest.mark.parametrize("test_case", from_dana_error_params, ids=lambda x: x["name"])
def test_basic_type_converter_from_dana_errors(test_case):
    """Test BasicTypeConverter.from_dana error handling."""
    # Arrange
    converter = BasicTypeConverter()

    # Act & Assert
    with pytest.raises(test_case["expected_error"]) as exc_info:
        converter.from_dana(test_case["dana_type"], test_case["input_value"])

    assert test_case["expected_message_contains"] in str(exc_info.value)


# Test parameters for complex type conversion
complex_type_params = [
    {
        "name": "custom_object_with_dict",
        "input_value": type("TestClass", (), {"attr": "value", "number": 42})(),
        "expected_type": DanaType.DICT,
        "expected_contains_keys": ["_type", "class", "data"],
    },
]


@pytest.mark.parametrize("test_case", complex_type_params, ids=lambda x: x["name"])
def test_basic_type_converter_complex_types(test_case):
    """Test BasicTypeConverter handling of complex Python objects."""
    # Arrange
    converter = BasicTypeConverter()

    # Act
    result_type, result_value = converter.to_dana(test_case["input_value"])

    # Assert
    assert result_type == test_case["expected_type"]
    if "expected_contains_keys" in test_case:
        for key in test_case["expected_contains_keys"]:
            assert key in result_value


# Test parameters for validate_and_convert function
validate_and_convert_params = [
    {
        "name": "valid_string",
        "value": "hello",
        "expected_type": str,
        "context": "",
        "should_pass": True,
        "expected_result": "hello",
    },
    {
        "name": "valid_int",
        "value": 42,
        "expected_type": int,
        "context": "parameter",
        "should_pass": True,
        "expected_result": 42,
    },
    {
        "name": "invalid_string_as_int",
        "value": "hello",
        "expected_type": int,
        "context": "argument",
        "should_pass": False,
        "expected_error": TypeError,
    },
    {
        "name": "invalid_none_as_string",
        "value": None,
        "expected_type": str,
        "context": "required field",
        "should_pass": False,
        "expected_error": TypeError,
    },
]


@pytest.mark.parametrize("test_case", validate_and_convert_params, ids=lambda x: x["name"])
def test_validate_and_convert(test_case):
    """Test validate_and_convert function with various inputs."""
    if test_case["should_pass"]:
        # Act
        result = validate_and_convert(test_case["value"], test_case["expected_type"], test_case["context"])

        # Assert
        assert result == test_case["expected_result"]
    else:
        # Act & Assert
        with pytest.raises(test_case["expected_error"]):
            validate_and_convert(test_case["value"], test_case["expected_type"], test_case["context"])


def test_basic_type_converter_round_trip():
    """Test that converting to Dana and back preserves data integrity."""
    # Arrange
    converter = BasicTypeConverter()
    test_data = [
        "string",
        42,
        3.14,
        True,
        False,
        None,
        [1, 2, 3],
        {"key": "value", "nested": {"inner": [1, 2]}},
    ]

    for original_value in test_data:
        # Act
        dana_type, dana_value = converter.to_dana(original_value)
        result_value = converter.from_dana(dana_type, dana_value)

        # Assert
        assert result_value == original_value


def test_basic_type_converter_set_conversion():
    """Test that sets are properly converted to lists."""
    # Arrange
    converter = BasicTypeConverter()
    original_set = {1, 2, 3, 4, 5}

    # Act
    dana_type, dana_value = converter.to_dana(original_set)

    # Assert
    assert dana_type == DanaType.LIST
    assert isinstance(dana_value, list)
    assert set(dana_value) == original_set


def test_basic_type_converter_tuple_conversion():
    """Test that tuples are properly converted to lists."""
    # Arrange
    converter = BasicTypeConverter()
    original_tuple = (1, "hello", True)

    # Act
    dana_type, dana_value = converter.to_dana(original_tuple)

    # Assert
    assert dana_type == DanaType.LIST
    assert isinstance(dana_value, list)
    assert dana_value == list(original_tuple)
