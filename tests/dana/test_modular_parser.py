"""Tests for the modular parser implementation."""

from opendxa.dana.language.ast import (
    Assignment,
    BinaryExpression,
    BinaryOperator,
    Conditional,
    FStringExpression,
    Identifier,
    LiteralExpression,
    LogLevel,
    LogStatement,
    Program,
    WhileLoop,
)
from opendxa.dana.language.parser import parse


def test_modular_parse_assignment():
    """Test parsing a simple assignment statement with the modular parser."""
    result = parse("temp.x = 42", type_check=False)
    assert result.is_valid
    assert len(result.errors) == 0

    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "temp.x"
    assert isinstance(stmt.value, LiteralExpression)
    assert stmt.value.literal.value == 42


def test_modular_parse_conditional():
    """Test parsing a conditional statement with the modular parser."""
    code = """
if private.x > 5:
    private.y = 10
else:
    private.y = 20
"""
    result = parse(code, type_check=False)
    assert result.is_valid
    assert len(result.errors) == 0

    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, Conditional)
    assert isinstance(stmt.condition, BinaryExpression)
    assert stmt.condition.operator == BinaryOperator.GREATER_THAN
    assert isinstance(stmt.condition.left, Identifier)
    assert stmt.condition.left.name == "private.x"
    assert isinstance(stmt.condition.right, LiteralExpression)
    assert stmt.condition.right.literal.value == 5

    # Check if body
    assert len(stmt.body) == 1
    assert isinstance(stmt.body[0], Assignment)
    assert stmt.body[0].target.name == "private.y"
    assert stmt.body[0].value.literal.value == 10

    # Check else body
    assert len(stmt.else_body) == 1
    assert isinstance(stmt.else_body[0], Assignment)
    assert stmt.else_body[0].target.name == "private.y"
    assert stmt.else_body[0].value.literal.value == 20


def test_modular_parse_fstring():
    """Test parsing an f-string with the modular parser."""
    result = parse('private.message = f"Hello, {private.name}"', type_check=False)
    assert result.is_valid
    assert len(result.errors) == 0

    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.message"
    assert isinstance(stmt.value, LiteralExpression)
    assert isinstance(stmt.value.literal.value, FStringExpression)

    # Check the f-string has the appropriate parts
    fstring = stmt.value.literal.value
    assert hasattr(fstring, "_is_fstring")
    assert hasattr(fstring, "_original_text")
    assert fstring._original_text == "Hello, {private.name}"


def test_modular_parse_log_statement():
    """Test parsing a log statement with the modular parser."""
    result = parse('log.info("This is a log message")', type_check=False)
    assert result.is_valid
    assert len(result.errors) == 0

    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, LogStatement)
    assert stmt.level == LogLevel.INFO
    assert isinstance(stmt.message, LiteralExpression)
    assert stmt.message.literal.value == "This is a log message"


def test_modular_parse_while_loop():
    """Test parsing a while loop with the modular parser."""
    code = """
while private.count < 10:
    temp.count = private.count + 1
    log.info("Count: " + private.count)
"""
    result = parse(code, type_check=False)
    assert result.is_valid
    assert len(result.errors) == 0

    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, WhileLoop)
    assert isinstance(stmt.condition, BinaryExpression)
    assert stmt.condition.operator == BinaryOperator.LESS_THAN
    assert isinstance(stmt.condition.left, Identifier)
    assert stmt.condition.left.name == "private.count"
    assert isinstance(stmt.condition.right, LiteralExpression)
    assert stmt.condition.right.literal.value == 10

    # Check body
    assert len(stmt.body) == 2
    assert isinstance(stmt.body[0], Assignment)
    assert stmt.body[0].target.name == "temp.count"
    assert isinstance(stmt.body[0].value, BinaryExpression)
    assert stmt.body[0].value.operator == BinaryOperator.ADD

    assert isinstance(stmt.body[1], LogStatement)
    assert stmt.body[1].level == LogLevel.INFO


def test_modular_parse_syntax_error():
    """Test that syntax errors are correctly reported."""
    result = parse("temp.x = ", type_check=False)
    assert not result.is_valid
    assert len(result.errors) == 1

    # Just verify we have a non-empty error message
    error = result.errors[0]
    assert str(error), "Error message should not be empty"


def test_modular_parse_complex_expression():
    """Test parsing complex expressions with correct precedence."""
    result = parse("private.result = 2 + 3 * 4", type_check=False)
    assert result.is_valid
    assert len(result.errors) == 0

    assert isinstance(result.program, Program)
    assert len(result.program.statements) == 1

    stmt = result.program.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.target.name == "private.result"

    # Should be structured as 2 + (3 * 4) due to precedence
    assert isinstance(stmt.value, BinaryExpression)
    assert stmt.value.operator == BinaryOperator.ADD
    assert isinstance(stmt.value.left, LiteralExpression)
    assert stmt.value.left.literal.value == 2

    assert isinstance(stmt.value.right, BinaryExpression)
    assert stmt.value.right.operator == BinaryOperator.MULTIPLY
    assert isinstance(stmt.value.right.left, LiteralExpression)
    assert stmt.value.right.left.literal.value == 3
    assert isinstance(stmt.value.right.right, LiteralExpression)
    assert stmt.value.right.right.literal.value == 4
