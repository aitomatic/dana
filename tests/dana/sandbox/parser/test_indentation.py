"""Test indentation handling in DANA parser."""

import pytest
from opendxa.dana.sandbox.parser.dana_parser import DanaParser

def test_basic_indentation():
    """Test basic indentation handling."""
    parser = DanaParser()
    code = """
private:x = 0
while private:x < 3:
    private:x = private:x + 1
    if private:x == 2:
        print("x is 2")
"""
    result = parser.parse(code)
    assert result is not None

def test_nested_indentation():
    """Test nested indentation handling."""
    parser = DanaParser()
    code = """
def test():
    x = 0
    while x < 3:
        if x == 1:
            print("x is 1")
        x = x + 1
"""
    result = parser.parse(code)
    assert result is not None

def test_mixed_indentation():
    """Test mixed indentation handling."""
    parser = DanaParser()
    code = """
if True:
    x = 1
    if x > 0:
        print("x is positive")
    else:
        print("x is not positive")
"""
    result = parser.parse(code)
    assert result is not None 