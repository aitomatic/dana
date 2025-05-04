"""Tests for DANA f-string functionality."""

from unittest.mock import patch

import pytest

from opendxa.dana.exceptions import ParseError, StateError
from opendxa.dana.language.ast import LogLevel
from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter


def test_basic_fstring():
    """Test basic f-string functionality."""
    interpreter = Interpreter(RuntimeContext())
    interpreter.set_log_level(LogLevel.INFO)  # Ensure INFO messages are printed

    # Test simple variable interpolation
    program = """
    name = "World"
    log(f"Hello {name}")
    """
    with patch("builtins.print") as mock_print:
        interpreter.execute_program(parse(program))
        mock_print.assert_called_once()
        assert "Hello World" in mock_print.call_args[0][0]

    # Test expression interpolation
    program = """
    x = 5
    y = 3
    log(f"Sum: {x + y}")
    """
    with patch("builtins.print") as mock_print:
        interpreter.execute_program(parse(program))
        mock_print.assert_called_once()
        assert "Sum: 8" in mock_print.call_args[0][0]

    # Test multiple interpolations
    program = """
    name = "Alice"
    age = 30
    log(f"Name: {name}, Age: {age}")
    """
    with patch("builtins.print") as mock_print:
        interpreter.execute_program(parse(program))
        mock_print.assert_called_once()
        assert "Name: Alice, Age: 30" in mock_print.call_args[0][0]


def test_undefined_variable_error():
    """Test f-string error handling for undefined variables."""
    interpreter = Interpreter(RuntimeContext())

    program = """
    log(f"Invalid: {invalid_var}")
    """
    try:
        interpreter.execute_program(parse(program))
        pytest.fail("Expected RuntimeError but got none")
    except StateError as e:
        error_msg = str(e).lower()
        assert "invalid_var" in error_msg
        assert "not found" in error_msg


def test_unmatched_braces_error():
    """Test f-string error handling for unmatched braces."""
    interpreter = Interpreter(RuntimeContext())

    program = """
    log(f"Unmatched: {x")
    """
    with pytest.raises(Exception) as exc_info:
        interpreter.execute_program(parse(program))
    error_msg = str(exc_info.value).lower()
    assert "unmatched" in error_msg
    assert "{" in error_msg


def test_invalid_expression_error():
    """Test f-string error handling for invalid expressions."""
    interpreter = Interpreter(RuntimeContext())

    program = """
    log(f"Invalid expr: {1 + 'string'}")
    """
    with pytest.raises(ParseError) as exc_info:
        interpreter.execute_program(parse(program))
    error_msg = str(exc_info.value).lower()
    assert "invalid" in error_msg
    assert "expression" in error_msg


def test_nested_fstring_error():
    """Test f-string error handling for nested f-strings."""
    interpreter = Interpreter(RuntimeContext())

    # First, test with undefined variable
    program = """
    log(f"Outer {f'Inner {x}'}")
    """
    try:
        interpreter.execute_program(parse(program))
        pytest.fail("Expected RuntimeError but got none")
    except StateError as e:
        error_msg = str(e).lower()
        assert "x" in error_msg
        assert "not found" in error_msg

    # Then test with defined variable
    program = """
    x = "test"
    log(f"Outer {f'Inner {x}'}")
    """
    interpreter.execute_program(parse(program))


def test_empty_fstring_expression_error():
    """Test f-string error handling for empty expressions."""
    interpreter = Interpreter(RuntimeContext())

    program = """
    log(f"Empty: {}")
    """
    with pytest.raises(ParseError) as exc_info:
        interpreter.execute_program(parse(program))
    error_msg = str(exc_info.value).lower()
    assert "empty" in error_msg
    assert "expression" in error_msg
