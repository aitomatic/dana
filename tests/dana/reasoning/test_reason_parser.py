"""Tests for the reason statement parser."""

import pytest

from opendxa.dana.language.parser import GrammarParser, ParseResult


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return GrammarParser()


def test_parse_simple_reason(parser):
    """Test parsing a simple reason statement."""
    code = 'private.result = reason("What is 2+2?")'
    parse_result = parser.parse(code)
    assert isinstance(parse_result, ParseResult)
    assert parse_result.is_valid
    assert len(parse_result.program.statements) == 1


def test_parse_reason_with_context(parser):
    """Test parsing a reason statement with context."""
    code = """
    private.context = {
        "temperature": 0.7,
        "max_tokens": 100
    }
    private.result = reason("What is 2+2?", context=private.context)
    """
    parse_result = parser.parse(code)
    assert isinstance(parse_result, ParseResult)
    assert parse_result.is_valid
    assert len(parse_result.program.statements) == 2


def test_parse_reason_with_invalid_context(parser):
    """Test parsing a reason statement with invalid context."""
    code = 'private.result = reason("What is 2+2?", context=42)'
    parse_result = parser.parse(code)
    assert isinstance(parse_result, ParseResult)
    assert parse_result.is_valid
    assert len(parse_result.program.statements) == 1
