"""Tests for the new Interpreter implementation in DANA."""

import pytest

from opendxa.dana.language.parser import parse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter, LogLevel


def test_new_interpreter_basic():
    """Test basic functionality of the new interpreter."""
    # Create interpreter with context
    context = RuntimeContext()
    interpreter = Interpreter(context)

    # Simple program
    program = """
    private.x = 42
    private.y = 10
    private.z = private.x + private.y
    """

    # Parse and execute
    parse_result = parse(program)
    interpreter.execute_program(parse_result)

    # Check results
    assert context.get("private.x") == 42
    assert context.get("private.y") == 10
    assert context.get("private.z") == 52


def test_new_interpreter_conditionals():
    """Test conditional statements in the new interpreter."""
    # Create interpreter
    context = RuntimeContext()
    interpreter = Interpreter(context)

    # Program with conditional logic
    program = """
    private.value = 5
    private.threshold = 10
    
    if private.value < private.threshold:
        private.result = "below"
    """

    # Parse and execute
    parse_result = parse(program)
    interpreter.execute_program(parse_result)

    # Check that conditional was evaluated correctly
    assert context.get("private.result") == "below"

    # Program with conditional that shouldn't execute
    program = """
    private.value = 15
    
    if private.value < private.threshold:
        private.result = "changed"
    """

    # Parse and execute
    parse_result = parse(program)
    interpreter.execute_program(parse_result)

    # Result should not be changed
    assert context.get("private.result") == "below"


def test_new_interpreter_error_handling():
    """Test error handling in the new interpreter."""
    # Create interpreter
    context = RuntimeContext()
    interpreter = Interpreter(context)

    # Program with an error (division by zero)
    program = """
    private.a = 10
    private.b = 0
    private.c = private.a / private.b
    """

    # Should raise an exception
    parse_result = parse(program)
    with pytest.raises(Exception) as excinfo:
        interpreter.execute_program(parse_result)

    # Error message should contain essential information
    assert "Division by zero" in str(excinfo.value)


def test_new_interpreter_log_level():
    """Test log level functionality in the new interpreter."""
    # Create interpreter
    context = RuntimeContext()
    interpreter = Interpreter(context)

    # Set log level to INFO
    interpreter.set_log_level(LogLevel.INFO)

    # Check log level in context
    assert context.get("system.log_level") == LogLevel.INFO.value

    # Change to DEBUG
    interpreter.set_log_level(LogLevel.DEBUG)

    # Check log level was changed
    assert context.get("system.log_level") == LogLevel.DEBUG.value
