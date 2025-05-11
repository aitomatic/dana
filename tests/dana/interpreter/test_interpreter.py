"""Tests for the DANA interpreter."""

import pytest

from opendxa.dana.exceptions import StateError
from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Identifier,
    Literal,
    LiteralExpression,
    Location,
    LogLevel,
    LogLevelSetStatement,
    Program,
)
from opendxa.dana.language.parser import ParseResult
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter
from opendxa.dana.runtime.log_manager import LEVEL_MAP, LogManager


def create_location(line: int, column: int, text: str = "") -> Location:
    """Helper to create location tuples."""
    return (line, column, text)


def test_arithmetic_operations():
    """Test basic arithmetic operations."""
    interpreter = Interpreter(RuntimeContext())

    # Addition: 5 + 3
    program = Program(
        [
            Assignment(
                target=Identifier("private.value"),
                value=BinaryExpression(
                    left=LiteralExpression(Literal(5)), operator=BinaryOperator.ADD, right=LiteralExpression(Literal(3))
                ),
            )
        ]
    )
    interpreter.execute_program(ParseResult(program=program))
    assert interpreter.context.get("private.value") == 8

    # Subtraction: 10 - 4
    program = Program(
        [
            Assignment(
                target=Identifier("private.value"),
                value=BinaryExpression(
                    left=LiteralExpression(Literal(10)), operator=BinaryOperator.SUBTRACT, right=LiteralExpression(Literal(4))
                ),
            )
        ]
    )
    interpreter.execute_program(ParseResult(program=program))
    assert interpreter.context.get("private.value") == 6

    # Multiplication: 6 * 7
    program = Program(
        [
            Assignment(
                target=Identifier("private.value"),
                value=BinaryExpression(
                    left=LiteralExpression(Literal(6)), operator=BinaryOperator.MULTIPLY, right=LiteralExpression(Literal(7))
                ),
            )
        ]
    )
    interpreter.execute_program(ParseResult(program=program))
    assert interpreter.context.get("private.value") == 42

    # Division: 20 / 5
    program = Program(
        [
            Assignment(
                target=Identifier("private.value"),
                value=BinaryExpression(
                    left=LiteralExpression(Literal(20)), operator=BinaryOperator.DIVIDE, right=LiteralExpression(Literal(5))
                ),
            )
        ]
    )
    interpreter.execute_program(ParseResult(program=program))
    assert interpreter.context.get("private.value") == 4


def test_division_by_zero():
    """Test division by zero raises RuntimeError with location information."""
    interpreter = Interpreter(RuntimeContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.value"),
                value=BinaryExpression(
                    left=LiteralExpression(Literal(10)),
                    operator=BinaryOperator.DIVIDE,
                    right=LiteralExpression(Literal(0)),
                    location=create_location(5, 10, "x = 10 / 0"),
                ),
            )
        ]
    )
    with pytest.raises(StateError) as exc_info:
        interpreter.execute_program(ParseResult(program=program))

    error_msg = str(exc_info.value)
    # Check that we have location information in the error message
    assert "line 5" in error_msg.lower(), "Error should include line number"
    assert "column 10" in error_msg.lower(), "Error should include column number"
    # Verify the error contains the source code context
    assert "10" in error_msg and "/" in error_msg and "0" in error_msg, "Error should include relevant source code"


def test_undefined_variable():
    """Test accessing undefined variable raises StateError with location information."""
    interpreter = Interpreter(RuntimeContext())
    program = Program(
        [
            Assignment(
                target=Identifier("private.value"),
                value=Identifier(name="undefined_var", location=create_location(3, 5, "x = undefined_var")),
            )
        ]
    )
    with pytest.raises(StateError) as exc_info:
        interpreter.execute_program(ParseResult(program=program))

    error_msg = str(exc_info.value)
    # Check that we have location information in the error message
    assert "line 3" in error_msg.lower(), "Error should include line number"
    assert "column 5" in error_msg.lower(), "Error should include column number"
    # Verify the error references the undefined variable name
    assert "undefined_var" in error_msg, "Error should mention the undefined variable name"


def test_string_concatenation():
    """Test string concatenation with different types."""
    interpreter = Interpreter(RuntimeContext())

    # String + String
    program = Program(
        [
            Assignment(
                target=Identifier("private.value"),
                value=BinaryExpression(
                    left=LiteralExpression(Literal("Hello ")), operator=BinaryOperator.ADD, right=LiteralExpression(Literal("World"))
                ),
            )
        ]
    )
    interpreter.execute_program(ParseResult(program=program))
    assert interpreter.context.get("private.value") == "Hello World"

    # String + Number
    program = Program(
        [
            Assignment(
                target=Identifier("private.value"),
                value=BinaryExpression(
                    left=LiteralExpression(Literal("Count: ")), operator=BinaryOperator.ADD, right=LiteralExpression(Literal(42))
                ),
            )
        ]
    )
    interpreter.execute_program(ParseResult(program=program))
    assert interpreter.context.get("private.value") == "Count: 42"


def test_expression_precedence():
    """Test operator precedence in expressions."""
    interpreter = Interpreter(RuntimeContext())

    # 2 + 3 * 4 should be 14 (not 20)
    program = Program(
        [
            Assignment(
                target=Identifier("private.value"),
                value=BinaryExpression(
                    left=LiteralExpression(Literal(2)),
                    operator=BinaryOperator.ADD,
                    right=BinaryExpression(
                        left=LiteralExpression(Literal(3)), operator=BinaryOperator.MULTIPLY, right=LiteralExpression(Literal(4))
                    ),
                ),
            )
        ]
    )
    interpreter.execute_program(ParseResult(program=program))
    assert interpreter.context.get("private.value") == 14


def test_log_statement():
    """Test log statement execution."""
    context = RuntimeContext()
    interpreter = Interpreter(context=context)
    LogManager.set_dana_log_level(LogLevel.INFO, context)  # Ensure INFO messages are printed by default

    # Test different log levels
    interpreter.debug("Debug message")
    interpreter.info("Info message")
    interpreter.warning("Warning message")
    interpreter.error("Error message")


def test_log_level_threshold():
    """Test that log messages respect the current log level threshold."""
    context = RuntimeContext()
    interpreter = Interpreter(context=context)

    # Set to WARN level
    LogManager.set_dana_log_level(LogLevel.WARN, context)

    # Test that INFO messages are not shown
    interpreter.info("This should not be shown")
    interpreter.warning("This should be shown")
    interpreter.error("This should be shown")


def test_log_level_set_statement():
    """Test log level set statement."""
    context = RuntimeContext()
    interpreter = Interpreter(context=context)

    # Test setting different log levels
    for level in [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR]:
        node = LogLevelSetStatement(level=level)
        interpreter.statement_executor.execute_log_level_set_statement(node)
        # Verify the log level was set by checking the actual logger level
        assert interpreter.logger.logger.level == LEVEL_MAP[level]


def test_print_statement(capfd):
    """Test that print statements work correctly."""
    # ... existing code ...
