"""Tests for the reason statement parser."""

import pytest

from opendxa.dana.sandbox.parser.dana_parser import DanaParser, Program


@pytest.fixture
def parser():
    """Create a fresh parser instance for each test."""
    return DanaParser()


def test_parse_simple_reason(parser):
    """Test parsing a simple reason statement."""
    code = 'private:result = reason("What is 2+2?")'
    program = parser.parse(code)
    assert isinstance(program, Program)
    assert len(program.statements) == 1


# The following tests are commented out because Dana does not support object/dict literals as assignment values.
# def test_parse_reason_with_context(parser):
#     """Test parsing a reason statement with context."""
#     code = textwrap.dedent('''
#         private:context = {
#             "temperature": 0.7,
#             "max_tokens": 100
#         }
#         private:result = reason("What is 2+2?", context=private:context)
#     ''')
#     program = parser.parse(code)
#     assert isinstance(program, Program)
#     assert len(program.statements) == 2

# def test_parse_reason_with_invalid_context(parser):
#     """Test parsing a reason statement with invalid context."""
#     code = 'private:result = reason("What is 2+2?", context=42)'
#     program = parser.parse(code)
#     assert isinstance(program, Program)
#     assert len(program.statements) == 1
