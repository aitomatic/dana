"""Unit tests for the DANA language parser."""

from opendxa.dana.language.ast import Assignment, LiteralExpression, LogStatement, Program
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
    assert stmt1.value.literal.value == 42

    # Check second statement
    stmt2 = result.program.statements[1]
    assert isinstance(stmt2, Assignment)
    assert stmt2.target.name == "temp.y"
    assert stmt2.value.literal.value == "test"

    # Check third statement
    stmt3 = result.program.statements[2]
    assert isinstance(stmt3, LogStatement)
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
