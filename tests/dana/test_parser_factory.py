"""Tests for the DANA parser factory."""

import pytest

from opendxa.dana.language.parser import parse as regex_parse
from opendxa.dana.language.parser_factory import get_parser, parse

try:
    from opendxa.dana.language.lark_parser import parse as lark_parse
    LARK_AVAILABLE = True
except ImportError:
    LARK_AVAILABLE = False


def test_get_default_parser():
    """Test getting the default parser."""
    # Default should be the regex parser
    parser = get_parser()
    assert parser == regex_parse


@pytest.mark.skipif(not LARK_AVAILABLE, reason="Lark parser not available")
def test_get_lark_parser():
    """Test getting the Lark parser if available."""
    parser = get_parser(use_lark=True)
    assert parser == lark_parse


def test_parse_with_default_parser():
    """Test parsing with the default (regex) parser."""
    # Simple assignment
    result = parse("private.x = 42")
    assert result.is_valid
    assert len(result.program.statements) == 1
    assert result.program.statements[0].target.name == "private.x"
    assert result.program.statements[0].value.literal.value == 42


def test_parse_with_explicit_regex_parser():
    """Test parsing with the explicitly specified regex parser."""
    # Simple assignment
    result = parse("private.x = 42", use_lark=False)
    assert result.is_valid
    assert len(result.program.statements) == 1
    assert result.program.statements[0].target.name == "private.x"
    assert result.program.statements[0].value.literal.value == 42


@pytest.mark.skipif(not LARK_AVAILABLE, reason="Lark parser not available")
def test_parse_with_lark_parser():
    """Test parsing with the Lark parser."""
    # This test is a placeholder that will need to be updated once
    # the Lark parser is fully implemented
    try:
        # For now, we're just testing that it doesn't crash
        result = parse("private.x = 42", use_lark=True)
        # Since the Lark parser is not fully implemented, this might return an empty program
        assert hasattr(result, 'program')
    except NotImplementedError:
        # Or it might raise NotImplementedError, which is also acceptable for now
        pass