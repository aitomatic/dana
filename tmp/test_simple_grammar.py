#!/usr/bin/env python3
"""
Simple test for string parsing issue.
"""

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def test_strings():
    parser = DanaParser()

    tests = [
        ("Double quotes", 'x = "hello"'),
        ("Single quotes", "x = 'hello'"),
        ("Basic assignment", "x = 42"),
        ("Typed assignment", "x: int = 42"),
        ("Function return type", "def test() -> int:\n    pass"),
    ]

    for test_name, code in tests:
        try:
            result = parser.parse(code, do_transform=False)
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")


if __name__ == "__main__":
    test_strings()
