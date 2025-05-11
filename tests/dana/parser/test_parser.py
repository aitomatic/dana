"""Unit tests for the DANA language parser."""

import pytest

from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Identifier,
    LiteralExpression,
    LogLevelSetStatement,
    LogStatement,
    Program,
)
from opendxa.dana.language.parser import GrammarParser, ParseResult


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return GrammarParser()


def test_parse_assignment(parser):
    """Test parsing a simple assignment statement."""
    result = parser.parse("temp.x = 42", type_check=False)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.temp.x"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.literal.value == 42


def test_parse_float_assignment(parser):
    """Test parsing a float assignment."""
    result = parser.parse("temp.x = 3.14", type_check=False)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.temp.x"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.literal.value == 3.14


def test_parse_arithmetic_expression(parser):
    """Test parsing arithmetic expressions."""
    result = parser.parse("temp.x = 5 + 3 * 2", type_check=False)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.temp.x"

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
    result = parser.parse("private.x = (5 + 3) * 2", type_check=False)
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
    result = parser.parse("private.x = 1.5 + 2.5 * 3.0", type_check=False)
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
    result = parser.parse('temp.msg = "Alice"', type_check=False)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.temp.msg"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.literal.value == "Alice"


def test_parse_log_statement(parser):
    """Test parsing a log statement."""
    result = parser.parse('log("Hello, world!")', type_check=False)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, LogStatement)
    assert isinstance(stmt.message, LiteralExpression)
    assert stmt.message.literal.value == "Hello, world!"


def test_parse_log_level_set_statement(parser):
    """Test parsing a log level set statement."""
    # Test with different log levels
    for level in ["debug", "info", "warn", "error"]:
        result = parser.parse(f'log.setLevel("{level}")', type_check=False)
        assert isinstance(result, ParseResult)
        assert isinstance(result.program, Program)
        assert len(result.program.statements) == 1
        assert not result.errors

        stmt = result.program.statements[0]
        assert isinstance(stmt, LogLevelSetStatement)
        assert stmt.level.value == level.upper()

    # Test invalid log level
    result = parser.parse('log.setLevel("invalid")', type_check=False)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) > 0
    stmt = result.program.statements[0]
    assert isinstance(stmt, LogLevelSetStatement)


def test_parse_multiple_statements(parser):
    """Test parsing multiple statements."""
    result = parser.parse('temp.x = 42\ntemp.y = "test"\nlog("done")', type_check=False)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 3
    assert not result.errors

    # Check first statement
    stmt1 = result.program.statements[0]
    assert isinstance(stmt1, Assignment)
    assert stmt1.target.name == "private.temp.x"
    assert isinstance(stmt1.value, LiteralExpression)
    assert stmt1.value.literal.value == 42

    # Check second statement
    stmt2 = result.program.statements[1]
    assert isinstance(stmt2, Assignment)
    assert stmt2.target.name == "private.temp.y"
    assert isinstance(stmt2.value, LiteralExpression)
    assert stmt2.value.literal.value == "test"

    # Check third statement
    stmt3 = result.program.statements[2]
    assert isinstance(stmt3, LogStatement)
    assert isinstance(stmt3.message, LiteralExpression)
    assert stmt3.message.literal.value == "done"


def test_parse_conditional_with_else(parser):
    """Test parsing a conditional statement with else."""
    code = """
    if private.x > 10:
        private.y = 20
    else:
        private.y = 30
    """
    result = parser.parse(code, type_check=False)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, ConditionalStatement)
    assert isinstance(stmt.condition, BinaryExpression)
    assert stmt.condition.operator == BinaryOperator.GREATER_THAN
    assert isinstance(stmt.condition.left, Identifier)
    assert stmt.condition.left.name == "private.x"
    assert isinstance(stmt.condition.right, LiteralExpression)
    assert stmt.condition.right.literal.value == 10

    assert len(stmt.then_block.statements) == 1
    assert len(stmt.else_block.statements) == 1


def test_parse_while_loop(parser):
    """Test parsing a while loop."""
    code = """
    while private.x < 10:
        private.x = private.x + 1
    """
    result = parser.parse(code, type_check=False)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, WhileStatement)
    assert isinstance(stmt.condition, BinaryExpression)
    assert stmt.condition.operator == BinaryOperator.LESS_THAN
    assert isinstance(stmt.condition.left, Identifier)
    assert stmt.condition.left.name == "private.x"
    assert isinstance(stmt.condition.right, LiteralExpression)
    assert stmt.condition.right.literal.value == 10

    assert len(stmt.body.statements) == 1


def test_parse_invalid_syntax(parser):
    """Test parsing invalid syntax."""
    # Test incomplete assignment
    result = parser.parse("temp.x =", type_check=False)
    assert not result.is_valid
    assert len(result.errors) > 0

    # Test missing left side
    result = parser.parse("= 42", type_check=False)
    assert not result.is_valid
    assert len(result.errors) > 0

    # Test invalid function call
    result = parser.parse("log()", type_check=False)
    assert not result.is_valid
    assert len(result.errors) > 0


def test_parse_bare_identifier(parser):
    """Test parsing a bare identifier."""
    result = parser.parse("private.x", type_check=False)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, ExpressionStatement)
    assert isinstance(stmt.expression, Identifier)
    assert stmt.expression.name == "private.x"


def test_parse_bare_identifier_with_type_check(parser):
    """Test parsing a bare identifier with type checking."""
    # First set up the variable
    setup_result = parser.parse("private.x = 42", type_check=True)
    assert setup_result.is_valid

    # Then try to access it
    result = parser.parse("private.x", type_check=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert not result.errors

    stmt = result.program.statements[0]
    assert isinstance(stmt, ExpressionStatement)
    assert isinstance(stmt.expression, Identifier)
    assert stmt.expression.name == "private.x"


def test_parse_bare_identifier_undefined(parser):
    """Test parsing a bare identifier that is undefined."""
    result = parser.parse("private.undefined_var", type_check=True)
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert len(result.errors) > 0  # Should have type error for undefined variable

    stmt = result.program.statements[0]
    assert isinstance(stmt, ExpressionStatement)
    assert isinstance(stmt.expression, Identifier)
    assert stmt.expression.name == "private.undefined_var"
