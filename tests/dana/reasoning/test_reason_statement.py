"""Tests for the reason statement."""

import pytest

from opendxa.dana.language.parser import GrammarParser, ParseResult


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return GrammarParser()


def test_parse_reason_statement(parser):
    """Test parsing a reason statement."""
    program = parser.parse('private.result = reason("What is the capital of France?")')
    assert isinstance(program, ParseResult)
    assert program.is_valid
    assert len(program.program.statements) == 1
