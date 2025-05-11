"""Tests for the modular interpreter implementation."""

from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Identifier,
    Literal,
    LiteralExpression,
    LogLevel,
    PrintStatement,
    Program,
)
from opendxa.dana.language.parser import ParseResult
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter
from opendxa.dana.runtime.log_manager import LogManager


def test_arithmetic_operations():
    """Test basic arithmetic operations with the modular interpreter."""
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


def test_log_statement():
    """Test log statement execution with the modular interpreter."""
    context = RuntimeContext()
    interpreter = Interpreter(context)
    LogManager.set_dana_log_level(LogLevel.INFO, context)  # Ensure INFO messages are printed

    # Test different log levels
    interpreter.debug("Debug message")
    interpreter.info("Info message")
    interpreter.warning("Warning message")
    interpreter.error("Error message")


def test_print_statement(capfd):
    """Test that print statements work correctly with the modular interpreter."""
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


def test_variable_resolution():
    """Test variable resolution in the modular interpreter."""
    interpreter = Interpreter(RuntimeContext())

    # Set variables in the private scope
    program = Program(
        [
            Assignment(target=Identifier("private.x"), value=LiteralExpression(Literal(10))),
            Assignment(target=Identifier("private.y"), value=LiteralExpression(Literal(20))),
        ]
    )
    interpreter.execute_program(ParseResult(program=program))

    # Check that variables are set correctly
    assert interpreter.context.get("private.x") == 10
    assert interpreter.context.get("private.y") == 20

    # Test variable resolution in binary expression
    program = Program(
        [
            Assignment(
                target=Identifier("private.z"),
                value=BinaryExpression(left=Identifier("private.x"), operator=BinaryOperator.ADD, right=Identifier("private.y")),
            )
        ]
    )
    interpreter.execute_program(ParseResult(program=program))
    assert interpreter.context.get("private.z") == 30
