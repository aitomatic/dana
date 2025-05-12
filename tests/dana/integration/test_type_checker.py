"""Tests for the DANA type checker."""

import pytest
from dana.sandbox.sandbox_context import SandboxContext

from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Identifier,
    Literal,
    LiteralExpression,
)
from opendxa.dana.language.parser import GrammarParser
from opendxa.dana.language.type_checker import DanaType, TypeChecker, TypeEnvironment
from opendxa.dana.sandbox.interpreter import Interpreter


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return GrammarParser()


@pytest.fixture
def type_environment():
    """Create a type environment for testing."""
    return TypeEnvironment()


def test_type_environment():
    """Test the TypeEnvironment class."""
    env = TypeEnvironment()

    # Test setting and getting types
    env.set("private.x", DanaType("int"))
    type_ = env.get("private.x")
    assert type_ is not None
    assert type_.name == "int"

    # Test parent environment
    child_env = TypeEnvironment(parent=env)
    type_ = child_env.get("private.x")
    assert type_ is not None
    assert type_.name == "int"


def test_literal_types():
    """Test type inference for literals."""
    checker = TypeChecker()

    # Test integer
    assert checker.check_literal_expression(LiteralExpression(Literal(42))).name == "int"

    # Test float
    assert checker.check_literal_expression(LiteralExpression(Literal(3.14))).name == "float"

    # Test string
    assert checker.check_literal_expression(LiteralExpression(Literal("hello"))).name == "string"

    # Test boolean
    assert checker.check_literal_expression(LiteralExpression(Literal(True))).name == "bool"
    assert checker.check_literal_expression(LiteralExpression(Literal(False))).name == "bool"

    # Test null
    assert checker.check_literal_expression(LiteralExpression(Literal(None))).name == "null"


def test_binary_expression_types():
    """Test type inference for binary expressions."""
    checker = TypeChecker()

    # Test arithmetic operators
    expr = BinaryExpression(left=LiteralExpression(Literal(5)), operator=BinaryOperator.ADD, right=LiteralExpression(Literal(3)))
    assert checker.check_binary_expression(expr).name == "int"

    # Test arithmetic with mixed types
    expr = BinaryExpression(left=LiteralExpression(Literal(5)), operator=BinaryOperator.ADD, right=LiteralExpression(Literal(3.14)))
    assert checker.check_binary_expression(expr).name == "float"

    # Test string concatenation
    expr = BinaryExpression(
        left=LiteralExpression(Literal("hello")), operator=BinaryOperator.ADD, right=LiteralExpression(Literal(" world"))
    )
    assert checker.check_binary_expression(expr).name == "string"

    # Test comparison operators
    expr = BinaryExpression(left=LiteralExpression(Literal(5)), operator=BinaryOperator.LESS_THAN, right=LiteralExpression(Literal(10)))
    assert checker.check_binary_expression(expr).name == "bool"

    # Test logical operators
    expr = BinaryExpression(left=LiteralExpression(Literal(True)), operator=BinaryOperator.AND, right=LiteralExpression(Literal(False)))
    assert checker.check_binary_expression(expr).name == "bool"


def test_assignment_types():
    """Test type checking for assignments."""
    checker = TypeChecker()

    # Test assignment of compatible types
    checker.environment.set("private.x", DanaType("int"))
    assignment = Assignment(target=Identifier("private.x"), value=LiteralExpression(Literal(42)))
    checker.check_assignment(assignment)  # Should not raise

    # Test assignment of incompatible types
    checker.environment.set("private.y", DanaType("string"))
    assignment = Assignment(target=Identifier("private.y"), value=LiteralExpression(Literal(42)))
    with pytest.raises(RuntimeError) as excinfo:
        checker.check_assignment(assignment)
    assert "Type mismatch" in str(excinfo.value)


def test_type_checking_integration(parser):
    """Test type checking integration with parser."""
    # Program with string concatenation
    program = 'private.x = "hello"\nprivate.y = private.x + 42  # String concatenation'

    # Parse with type checking enabled
    result = parser.parse(program, type_check=True)

    # Parse without type checking
    result_no_check = parser.parse(program, type_check=False)

    # Both should be valid
    assert result.is_valid
    assert result_no_check.is_valid


def test_logical_operator_type_checking():
    """Test type checking for logical operators."""
    checker = TypeChecker()

    # Create a binary expression with non-boolean left operand
    expr = BinaryExpression(left=LiteralExpression(Literal(42)), operator=BinaryOperator.AND, right=LiteralExpression(Literal(True)))

    # This should raise a RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        checker.check_binary_expression(expr)
    assert "must be boolean" in str(excinfo.value)


def test_comprehensive_type_checking(parser):
    """Test type checking on a more complex program."""
    program = 'private.a = 10\nprivate.b = 20.5\nprivate.c = private.a + private.b  # Should be float\nprivate.d = "hello"\nprivate.e = private.d + " world"  # Should be string\nprivate.f = private.a < private.b  # Should be bool'

    # Parse with type checking enabled
    result = parser.parse(program, type_check=True)

    # Should be valid
    assert result.is_valid
    assert len(result.errors) == 0

    # We should be able to execute the program
    context = SandboxContext()
    interpreter = Interpreter.new(context)

    # This should execute without errors
    interpreter.execute_program(result)

    # Verify the values
    assert context.get("private.a") == 10
    assert context.get("private.b") == 20.5
    assert context.get("private.c") == 30.5
    assert context.get("private.d") == "hello"
    assert context.get("private.e") == "hello world"
    assert bool(context.get("private.f"))
