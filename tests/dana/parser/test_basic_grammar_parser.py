"""Basic tests for the DANA parser.

This module contains simple tests to verify that the parser works correctly
for basic DANA syntax.
"""

import pytest

from opendxa.dana.language.ast import Identifier
from opendxa.dana.language.parser import parse


def test_simple_assignment():
    """Test parsing a simple assignment."""
    code = "x = 42"
    result = parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_string_literals():
    """Test parsing string literals with both quote styles."""
    # Test double quotes
    code = 'message = "Hello, world!"'
    result = parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1

    # Test single quotes
    code = "name = 'Alice'"
    result = parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_nested_identifier():
    """Test parsing nested identifiers."""
    code = "private.user.name = 'Bob'"
    result = parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_simple_conditional():
    """Test parsing a simple conditional statement."""
    code = """if x > 10:
    log("x is greater than 10")
"""
    result = parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_conditional_with_else():
    """Test parsing a conditional with an else clause."""
    code = """if x > 10:
    log("x is greater than 10")
else:
    log("x is not greater than 10")
"""
    result = parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1


def test_bare_identifier():
    """Test parsing a bare identifier as a statement."""
    code = "private.x"
    result = parse(code, type_check=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    assert isinstance(result.program.statements[0], Identifier)
    assert result.program.statements[0].name == "private.x"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
