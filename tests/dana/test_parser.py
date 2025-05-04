"""Unit tests for the DANA language parser."""

from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    LiteralExpression,
    LogLevelSetStatement,
    LogStatement,
    Program,
)
from opendxa.dana.language.parser import ParseResult, parse


def test_parse_assignment():
    """Test parsing a simple assignment statement."""
    result = parse("temp.x = 42")
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert result.error is None

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "temp.x"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.literal.value == 42


def test_parse_float_assignment():
    """Test parsing a float assignment."""
    result = parse("temp.x = 3.14")
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert result.error is None

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "temp.x"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.literal.value == 3.14


def test_parse_arithmetic_expression():
    """Test parsing arithmetic expressions."""
    result = parse("temp.x = 5 + 3 * 2")
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert result.error is None

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "temp.x"

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


def test_parse_parenthetical_expression():
    """Test parsing expressions with parentheses."""
    result = parse("temp.x = (5 + 3) * 2")
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert result.error is None

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "temp.x"

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


def test_parse_mixed_arithmetic():
    """Test parsing mixed arithmetic expressions."""
    result = parse("temp.x = 1.5 + 2.5 * 3.0")
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert result.error is None

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "temp.x"

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


def test_parse_string_assignment():
    """Test parsing a string assignment."""
    result = parse('temp.msg = "Alice"')
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert result.error is None

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "temp.msg"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.literal.value == "Alice"


def test_parse_log_statement():
    """Test parsing a log statement."""
    result = parse('log("Hello, world!")')
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1
    assert result.error is None

    stmt = result.program.statements[0]
    assert isinstance(stmt, LogStatement)
    assert isinstance(stmt.message, LiteralExpression)
    assert stmt.message.literal.value == "Hello, world!"


def test_parse_log_level_set_statement():
    """Test parsing a log level set statement."""
    # Test with different log levels
    for level in ["debug", "info", "warn", "error"]:
        result = parse(f'log.setLevel("{level}")')
        assert isinstance(result, ParseResult)
        assert isinstance(result.program, Program)
        assert len(result.program.statements) == 1
        assert result.error is None

        stmt = result.program.statements[0]
        assert isinstance(stmt, LogLevelSetStatement)
        assert stmt.level.value == level.upper()

    # Test invalid log level
    result = parse('log.setLevel("invalid")')
    assert isinstance(result, ParseResult)
    assert result.error is not None
    assert "Invalid log level" in str(result.error)


def test_parse_multiple_statements():
    """Test parsing multiple statements."""
    result = parse(
        """
        temp.x = 42
        temp.y = "test"
        log("done")
    """
    )
    assert isinstance(result, ParseResult)
    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 3
    assert result.error is None

    # Check first statement
    stmt1 = result.program.statements[0]
    assert isinstance(stmt1, Assignment)
    assert stmt1.target.name == "temp.x"
    assert isinstance(stmt1.value, LiteralExpression)
    assert stmt1.value.literal.value == 42

    # Check second statement
    stmt2 = result.program.statements[1]
    assert isinstance(stmt2, Assignment)
    assert stmt2.target.name == "temp.y"
    assert isinstance(stmt2.value, LiteralExpression)
    assert stmt2.value.literal.value == "test"

    # Check third statement
    stmt3 = result.program.statements[2]
    assert isinstance(stmt3, LogStatement)
    assert isinstance(stmt3.message, LiteralExpression)
    assert stmt3.message.literal.value == "done"


def test_parse_invalid_syntax():
    """Test parsing invalid syntax."""
    result = parse("temp.x =")
    assert isinstance(result, ParseResult)
    assert result.error is not None

    result = parse("= 42")
    assert isinstance(result, ParseResult)
    assert result.error is not None

    result = parse("log()")
    assert isinstance(result, ParseResult)
    assert result.error is not None
