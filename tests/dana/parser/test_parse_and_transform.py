"""Unit tests for the DANA language parser."""

import pytest

from opendxa.dana.parser.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    Identifier,
    LiteralExpression,
    Program,
    WhileLoop,
)
from opendxa.dana.parser.dana_parser import DanaParser, ParseResult


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return DanaParser()


def test_parse_assignment(parser):
    """Test parsing a simple assignment statement."""
    result = parser.parse("x = 42", do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.x"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.literal.value == 42


def test_parse_float_assignment(parser):
    """Test parsing a float assignment."""
    result = parser.parse("x = 3.14", do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.x"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.literal.value == 3.14


def test_parse_arithmetic_expression(parser):
    """Test parsing arithmetic expressions."""
    result = parser.parse("x = 5 + 3 * 2", do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.x"

    # Check the expression structure
    expr = stmt.value
    assert isinstance(expr, BinaryExpression)
    assert expr.operator == BinaryOperator.ADD
    assert isinstance(expr.left, LiteralExpression)
    assert expr.left.literal.value == 5

    assert isinstance(expr.right, BinaryExpression)
    assert expr.right.operator == BinaryOperator.MULTIPLY
    assert isinstance(expr.right.left, LiteralExpression)
    assert expr.right.left.literal.value == 3
    assert isinstance(expr.right.right, LiteralExpression)
    assert expr.right.right.literal.value == 2


def test_parse_parenthetical_expression(parser):
    """Test parsing expressions with parentheses."""
    result = parser.parse("private.x = (5 + 3) * 2", do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.x"

    # Check the expression structure
    expr = stmt.value
    assert isinstance(expr, BinaryExpression)
    assert expr.operator == BinaryOperator.MULTIPLY

    # Check the parenthetical part
    assert isinstance(expr.left, BinaryExpression)
    assert expr.left.operator == BinaryOperator.ADD
    assert isinstance(expr.left.left, LiteralExpression)
    assert expr.left.left.literal.value == 5
    assert isinstance(expr.left.right, LiteralExpression)
    assert expr.left.right.literal.value == 3

    # Check the right part
    assert isinstance(expr.right, LiteralExpression)
    assert expr.right.literal.value == 2


def test_parse_mixed_arithmetic(parser):
    """Test parsing mixed arithmetic expressions."""
    result = parser.parse("private.x = 1.5 + 2.5 * 3.0", do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.x"

    # Check the expression structure
    expr = stmt.value
    assert isinstance(expr, BinaryExpression)
    assert expr.operator == BinaryOperator.ADD
    assert isinstance(expr.left, LiteralExpression)
    assert expr.left.literal.value == 1.5

    assert isinstance(expr.right, BinaryExpression)
    assert expr.right.operator == BinaryOperator.MULTIPLY
    assert isinstance(expr.right.left, LiteralExpression)
    assert expr.right.left.literal.value == 2.5
    assert isinstance(expr.right.right, LiteralExpression)
    assert expr.right.right.literal.value == 3.0


def test_parse_string_assignment(parser):
    """Test parsing a string assignment."""
    result = parser.parse('msg = "Alice"', do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "local.msg"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.literal.value == "Alice"


def test_parse_multiple_statements(parser):
    """Test parsing multiple statements."""
    result = parser.parse('x = 42\ny = "test"\nlog("done")', do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 3
    assert not result.errors

    # Check first statement
    stmt1 = result.program.statements[0]
    assert isinstance(stmt1, Assignment)
    assert stmt1.target.name == "local.x"
    assert isinstance(stmt1.value, LiteralExpression)
    assert stmt1.value.literal.value == 42

    # Check second statement
    stmt2 = result.program.statements[1]
    assert isinstance(stmt2, Assignment)
    assert stmt2.target.name == "local.y"
    assert isinstance(stmt2.value, LiteralExpression)
    assert stmt2.value.literal.value == "test"

    # Check third statement (should be an assignment or valid statement per grammar)
    stmt3 = result.program.statements[2]
    assert isinstance(stmt3, Assignment) or isinstance(stmt3, LiteralExpression)


def test_parse_conditional_with_else(parser):
    """Test parsing a conditional statement with else."""
    code = """
    if private.x > 10:
        private.y = 20
    else:
        private.y = 30
    """
    result = parser.parse(code, do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Conditional)
    assert isinstance(stmt.condition, BinaryExpression)
    assert stmt.condition.operator == BinaryOperator.GREATER_THAN
    assert isinstance(stmt.condition.left, Identifier)
    assert stmt.condition.left.name == "private.x"
    assert isinstance(stmt.condition.right, LiteralExpression)
    assert stmt.condition.right.literal.value == 10

    assert len(stmt.body) == 1
    assert len(stmt.else_body) == 1


def test_parse_while_loop(parser):
    """Test parsing a while loop."""
    code = """
    while private.x < 10:
        private.x = private.x + 1
    """
    result = parser.parse(code, do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, WhileLoop)
    assert isinstance(stmt.condition, BinaryExpression)
    assert stmt.condition.operator == BinaryOperator.LESS_THAN
    assert isinstance(stmt.condition.left, Identifier)
    assert stmt.condition.left.name == "private.x"
    assert isinstance(stmt.condition.right, LiteralExpression)
    assert stmt.condition.right.literal.value == 10

    assert len(stmt.body) == 1


def test_parse_invalid_syntax(parser):
    """Test parsing invalid syntax."""
    # Test incomplete assignment
    result = parser.parse("local.x =", do_type_check=False, do_transform=True)
    assert not result.is_valid
    assert len(result.errors) > 0

    # Test missing left side
    result = parser.parse("= 42", do_type_check=False, do_transform=True)
    assert not result.is_valid
    assert len(result.errors) > 0

    # Test invalid function call
    result = parser.parse("log()", do_type_check=False, do_transform=True)
    assert not result.is_valid
    assert len(result.errors) > 0


def test_parse_bare_identifier(parser):
    """Test parsing a bare identifier."""
    result = parser.parse("private.x", do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Identifier)
    assert stmt.name == "private.x"


def test_parse_bare_identifier_with_type_check(parser):
    """Test parsing a bare identifier with type checking."""
    # First set up the variable
    setup_result = parser.parse("private.x = 42", do_type_check=True, do_transform=True)
    assert setup_result.is_valid

    # Then try to access it
    result = parser.parse("private.x", do_type_check=True, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Identifier)
    assert stmt.name == "private.x"


def test_parse_bare_identifier_undefined(parser):
    """Test parsing a bare identifier that is undefined."""
    result = parser.parse("private.undefined_var", do_type_check=True, do_transform=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert len(result.errors) > 0  # Should have type error for undefined variable

    stmt = result.program.statements[0]
    assert isinstance(stmt, Identifier)
    assert stmt.name == "private.undefined_var"


def test_parse_fstring(parser):
    """Test parsing f-strings with embedded expressions and multiple parts."""
    # Simple f-string with one embedded expression
    result = parser.parse('private.message = f"Hello, {private.name}"', do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1

    # F-string with multiple embedded expressions and text
    code = 'private.msg = f"Sum: {private.x + private.y}, Product: {private.x * private.y}"'
    result = parser.parse(code, do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1

    # F-string with only text (no expressions)
    code = 'private.greeting = f"Hello, world!"'
    result = parser.parse(code, do_type_check=False, do_transform=True)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1
