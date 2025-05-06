"""Tests for the DANA interpreter."""

from unittest.mock import patch

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
    LogStatement,
    Program,
)
from opendxa.dana.language.parser import ParseResult
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter


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
    """Test division by zero raises RuntimeError with location."""
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
    error_lines = error_msg.splitlines()

    # Check structure: should have at least 3 parts
    assert len(error_lines) >= 3, f"Expected at least 3 lines in error message, got {len(error_lines)}"

    # Check content of each part, ignoring exact whitespace
    # 1. Error description
    assert "Division by zero" in error_lines[0]

    # 2. Location header - check essential info
    assert "line 5" in error_lines[1].lower()
    assert "column 10" in error_lines[1].lower()

    # 3. Source line - check essential content
    source_line = error_lines[2].strip()
    assert "10" in source_line
    assert "/" in source_line
    assert "0" in source_line


def test_undefined_variable():
    """Test accessing undefined variable raises RuntimeError with location."""
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
    error_lines = error_msg.splitlines()

    # Check structure: should have at least 3 parts
    assert len(error_lines) >= 3, f"Expected at least 3 lines in error message, got {len(error_lines)}"

    # Check content of each part, ignoring exact whitespace
    # 1. Error description
    assert "undefined_var" in error_lines[0].lower()
    assert "not found" in error_lines[0].lower() or "undefined" in error_lines[0].lower()

    # 2. Location header - check essential info
    assert "line 3" in error_lines[1].lower()
    assert "column 5" in error_lines[1].lower()

    # 3. Source line - check essential content
    source_line = error_lines[2].strip()
    assert "undefined_var" in source_line


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
    interpreter = Interpreter(RuntimeContext())
    interpreter.set_log_level(LogLevel.INFO)  # Ensure INFO messages are printed by default

    # Test default INFO level
    with patch("builtins.print") as mock_print:
        program = Program([LogStatement(message=LiteralExpression(Literal("Test message")))])
        interpreter.execute_program(ParseResult(program=program))
        mock_print.assert_called_once()
        assert "INFO" in mock_print.call_args[0][0]
        assert "Test message" in mock_print.call_args[0][0]

    # Test explicit levels
    interpreter.set_log_level(LogLevel.DEBUG)  # Set log level to DEBUG to see all messages
    with patch("builtins.print") as mock_print:
        program = Program(
            [
                LogStatement(message=LiteralExpression(Literal("Debug message")), level=LogLevel.DEBUG),
                LogStatement(message=LiteralExpression(Literal("Info message")), level=LogLevel.INFO),
                LogStatement(message=LiteralExpression(Literal("Warn message")), level=LogLevel.WARN),
                LogStatement(message=LiteralExpression(Literal("Error message")), level=LogLevel.ERROR),
            ]
        )
        interpreter.execute_program(ParseResult(program=program))
        assert mock_print.call_count == 4
        assert "DEBUG" in mock_print.call_args_list[0][0][0]
        assert "INFO" in mock_print.call_args_list[1][0][0]
        assert "WARN" in mock_print.call_args_list[2][0][0]
        assert "ERROR" in mock_print.call_args_list[3][0][0]


def test_log_level_threshold():
    """Test log level threshold filtering."""
    interpreter = Interpreter(RuntimeContext())

    # Set log level to WARN
    interpreter.set_log_level(LogLevel.WARN)

    with patch("builtins.print") as mock_print:
        program = Program(
            [
                LogStatement(message=LiteralExpression(Literal("Debug message")), level=LogLevel.DEBUG),
                LogStatement(message=LiteralExpression(Literal("Info message")), level=LogLevel.INFO),
                LogStatement(message=LiteralExpression(Literal("Warn message")), level=LogLevel.WARN),
                LogStatement(message=LiteralExpression(Literal("Error message")), level=LogLevel.ERROR),
            ]
        )
        interpreter.execute_program(ParseResult(program=program))
        assert mock_print.call_count == 2  # Only WARN and ERROR should be printed
        assert "WARN" in mock_print.call_args_list[0][0][0]
        assert "ERROR" in mock_print.call_args_list[1][0][0]


def test_log_level_set_statement():
    """Test log level set statement execution."""
    interpreter = Interpreter(RuntimeContext())

    # Test setting different log levels
    for level in [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR]:
        program = Program([LogLevelSetStatement(level=level)])
        interpreter.execute_program(ParseResult(program=program))
        assert interpreter.context.get("system.log_level") == level.value

        # Verify the log level affects message filtering
        with patch("builtins.print") as mock_print:
            program = Program(
                [
                    LogStatement(message=LiteralExpression(Literal("Debug message")), level=LogLevel.DEBUG),
                    LogStatement(message=LiteralExpression(Literal("Info message")), level=LogLevel.INFO),
                    LogStatement(message=LiteralExpression(Literal("Warn message")), level=LogLevel.WARN),
                    LogStatement(message=LiteralExpression(Literal("Error message")), level=LogLevel.ERROR),
                ]
            )
            interpreter.execute_program(ParseResult(program=program))
            # Count how many messages should be printed based on the level
            level_priorities = {LogLevel.DEBUG: 0, LogLevel.INFO: 1, LogLevel.WARN: 2, LogLevel.ERROR: 3}
            expected_count = sum(
                1
                for log_level in [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR]
                if level_priorities[log_level] >= level_priorities[level]
            )
            assert mock_print.call_count == expected_count


def test_print_statement(capfd):
    """Test that print statements work correctly."""
    from opendxa.dana.language.ast import PrintStatement
    from opendxa.dana.language.parser import parse
    
    # Create an interpreter
    context = RuntimeContext()
    interpreter = Interpreter(context)
    
    # Execute a program with a print statement using AST nodes directly
    program = Program(
        [
            Assignment(target=Identifier("private.x"), value=LiteralExpression(Literal(42))),
            PrintStatement(message=Identifier("private.x")),
            PrintStatement(message=LiteralExpression(Literal("Hello, world!"))),
        ]
    )
    interpreter.execute_program(ParseResult(program=program))
    
    # Check the captured output
    out, err = capfd.readouterr()
    assert "42" in out
    assert "Hello, world!" in out
    
    # Test using the parser
    program_text = "y = 100\nprint(y)\nprint(\"Testing print\")"
    result = parse(program_text, type_check=False)
    interpreter.execute_program(result)
    
    # Check output again
    out, err = capfd.readouterr()
    assert "100" in out
    assert "Testing print" in out


def test_state_management():
    """Test state management in the interpreter."""
    interpreter = Interpreter(RuntimeContext())

    # Set multiple values
    program = Program(
        [
            Assignment(target=Identifier("private.config.value1"), value=LiteralExpression(Literal(42))),
            Assignment(target=Identifier("private.config.value2"), value=LiteralExpression(Literal("test"))),
            Assignment(target=Identifier("public.state.counter"), value=LiteralExpression(Literal(100))),
        ]
    )
    interpreter.execute_program(ParseResult(program=program))

    # Verify values
    assert interpreter.context.get("private.config.value1") == 42
    assert interpreter.context.get("private.config.value2") == "test"
    assert interpreter.context.get("public.state.counter") == 100

    # Update existing value
    program = Program([Assignment(target=Identifier("private.config.value1"), value=LiteralExpression(Literal(99)))])
    interpreter.execute_program(ParseResult(program=program))
    assert interpreter.context.get("private.config.value1") == 99
