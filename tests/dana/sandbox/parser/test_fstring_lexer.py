"""Tests for F-string lexing in DANA language."""

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def test_fstring_lexer():
    """Test that our lexer correctly recognizes f-strings."""
    # Test with a parser that explicitly loads the grammar from disk
    parser = DanaParser(reload_grammar=True)

    # Simple test case with f-string
    code = 'result = f"Hello, {name}"'
    tree = parser.parse(code + "\n", do_transform=False)
    # Basic structure check
    assert "assignment" in str(tree)

    # Test f-string that starts with expression
    code2 = 'result = f"{name}"'
    tree2 = parser.parse(code2 + "\n", do_transform=False)
    # Basic structure check
    assert "assignment" in str(tree2)

    # Test f-string that starts with expression followed by text
    code3 = 'result = f"{name} suffix"'
    tree3 = parser.parse(code3 + "\n", do_transform=False)
    # Basic structure check
    assert "assignment" in str(tree3)
