"""Tests for DANA scope resolution and variable handling."""

from unittest.mock import patch

import pytest

from opendxa.dana.exceptions import StateError
from opendxa.dana.language.ast import LogLevel
from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter


def test_variable_scope_resolution():
    """Test that variables are properly scoped with and without explicit scope prefixes."""
    interpreter = Interpreter(RuntimeContext())

    # Test explicit scope
    program = """
    private.x = 42
    log(f"Value: {private.x}")
    """
    with patch("builtins.print") as mock_print:
        interpreter.set_log_level(LogLevel.INFO)
        interpreter.execute_program(parse(program))
        mock_print.assert_called_once()
        assert "42" in mock_print.call_args[0][0]
        assert interpreter.context.get("private.x") == 42

    # Test implicit private scope
    program2 = """
    x = 42
    log(f"Value: {x}")
    """
    with patch("builtins.print") as mock_print:
        interpreter.set_log_level(LogLevel.INFO)
        interpreter.execute_program(parse(program2))
        mock_print.assert_called_once()
        assert "42" in mock_print.call_args[0][0]
        assert interpreter.context.get("private.x") == 42


def test_fstring_variable_resolution():
    """Test that variables in f-strings are properly resolved with correct scoping."""
    interpreter = Interpreter(RuntimeContext())

    # Test explicit scope in f-string
    program = """
    private.name = "Alice"
    log(f"Name: {private.name}")
    """
    with patch("builtins.print") as mock_print:
        interpreter.set_log_level(LogLevel.INFO)
        interpreter.execute_program(parse(program))
        mock_print.assert_called_once()
        assert "Alice" in mock_print.call_args[0][0]
        assert interpreter.context.get("private.name") == "Alice"

    # Test implicit scope in f-string
    program2 = """
    name = "Bob"
    log(f"Name: {name}")
    """
    with patch("builtins.print") as mock_print:
        interpreter.set_log_level(LogLevel.INFO)
        interpreter.execute_program(parse(program2))
        mock_print.assert_called_once()
        assert "Bob" in mock_print.call_args[0][0]
        assert interpreter.context.get("private.name") == "Bob"


def test_fstring_error_location():
    """Test that errors in f-strings report the correct location of the problematic variable."""
    interpreter = Interpreter(RuntimeContext())

    # Test undefined variable location in f-string
    program = """
    log(f"Value: {undefined_var}")
    """
    with pytest.raises(StateError) as exc_info:
        interpreter.execute_program(parse(program))
    error_msg = str(exc_info.value)
    assert "undefined_var" in error_msg.lower()
    assert "not found" in error_msg.lower()

    # Test undefined scoped variable location
    program2 = """
    log(f"Value: {private.undefined_var}")
    """
    with pytest.raises(StateError) as exc_info:
        interpreter.execute_program(parse(program2))
    error_msg = str(exc_info.value)
    assert "private.undefined_var" in error_msg.lower()
    assert "not found" in error_msg.lower()


def test_nested_scope_resolution():
    """Test that deeply nested scopes are properly resolved."""
    interpreter = Interpreter(RuntimeContext())

    program = """
    private.config.settings.value = 42
    x = private.config.settings.value
    log(f"Value: {private.config.settings.value}")
    """
    with patch("builtins.print") as mock_print:
        interpreter.set_log_level(LogLevel.INFO)
        interpreter.execute_program(parse(program))
        mock_print.assert_called_once()
        assert "42" in mock_print.call_args[0][0]
        assert interpreter.context.get("private.config.settings.value") == 42
        assert interpreter.context.get("private.x") == 42


def test_variable_shadowing():
    """Test that variables with same name in different scopes don't interfere."""
    interpreter = Interpreter(RuntimeContext())

    program = """
    x = 42  # private.x
    public.x = 100  # group.x
    log(f"Private: {x}, Public: {public.x}")
    """
    with patch("builtins.print") as mock_print:
        interpreter.set_log_level(LogLevel.INFO)
        interpreter.execute_program(parse(program))
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        assert "42" in output
        assert "100" in output
        assert interpreter.context.get("private.x") == 42
        assert interpreter.context.get("public.x") == 100
