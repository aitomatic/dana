"""Basic tests for the DANA parser.

This module contains simple tests to verify that the parser works correctly
for basic DANA syntax.
"""

import pytest

from opendxa.dana.language.ast import Identifier
from opendxa.dana.language.parser import GrammarParser, ParseResult


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return GrammarParser()


def test_parse_simple_assignment(parser):
    """Test parsing a simple assignment."""
    code = "private.x = 42"
    result = parser.parse(code, type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_parse_string_assignment(parser):
    """Test parsing a string assignment."""
    code = 'private.message = "Hello, world!"'
    result = parser.parse(code, type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_parse_float_assignment(parser):
    """Test parsing a float assignment."""
    code = "private.pi = 3.14159"
    result = parser.parse(code, type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_parse_boolean_assignment(parser):
    """Test parsing a boolean assignment."""
    code = "private.is_valid = true"
    result = parser.parse(code, type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_parse_arithmetic_expression(parser):
    """Test parsing arithmetic expressions."""
    code = "private.result = 2 + 3 * 4"
    result = parser.parse(code, type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_parse_comparison_expression(parser):
    """Test parsing comparison expressions."""
    code = "private.is_greater = 5 > 3"
    result = parser.parse(code, type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_parse_logical_expression(parser):
    """Test parsing logical expressions."""
    code = "private.is_valid = true and false"
    result = parser.parse(code, type_check=False)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_string_literals():
    """Test parsing string literals with both quote styles."""
    # Test double quotes
    code = 'message = "Hello, world!"'
    result = parser.parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1

    # Test single quotes
    code = "name = 'Alice'"
    result = parser.parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_nested_identifier():
    """Test parsing nested identifiers."""
    code = "private.user.name = 'Bob'"
    result = parser.parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_simple_conditional():
    """Test parsing a simple conditional statement."""
    code = """if x > 10:
    log("x is greater than 10")
"""
    result = parser.parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_conditional_with_else():
    """Test parsing a conditional with an else clause."""
    code = """if x > 10:
    log("x is greater than 10")
else:
    log("x is not greater than 10")
"""
    result = parser.parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_bare_identifier():
    """Test parsing a bare identifier as a statement."""
    code = "private.x"
    result = parser.parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    assert isinstance(result.program.statements[0], Identifier)
    assert result.program.statements[0].name == "private.x"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
