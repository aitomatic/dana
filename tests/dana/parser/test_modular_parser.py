"""Tests for the modular parser implementation."""

import pytest

from opendxa.dana.language.parser import GrammarParser, ParseResult


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return GrammarParser()


def test_parse_simple_assignment(parser):
    """Test parsing a simple assignment."""
    result = parser.parse("private.x = 42", type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_parse_multiple_statements(parser):
    """Test parsing multiple statements."""
    code = """
    private.x = 42
    private.y = "test"
    log("done")
    """
    result = parser.parse(code, type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 3


def test_parse_fstring(parser):
    """Test parsing f-strings."""
    result = parser.parse('private.message = f"Hello, {private.name}"', type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_parse_log_statement(parser):
    """Test parsing log statements."""
    result = parser.parse('log.info("This is a log message")', type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_parse_conditional(parser):
    """Test parsing conditional statements."""
    code = """
    if private.x > 10:
        private.y = 20
    else:
        private.y = 30
    """
    result = parser.parse(code, type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_parse_invalid_syntax(parser):
    """Test parsing invalid syntax."""
    result = parser.parse("temp.x = ", type_check=False)
    assert not result.is_valid
    assert len(result.errors) > 0


def test_parse_arithmetic(parser):
    """Test parsing arithmetic expressions."""
    result = parser.parse("private.result = 2 + 3 * 4", type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_parse_bare_identifier(parser):
    """Test parsing a bare identifier."""
    result = parser.parse("private.x", type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1
