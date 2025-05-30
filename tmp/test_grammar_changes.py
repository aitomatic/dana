#!/usr/bin/env python3
"""
Test script for Dana type annotation grammar changes.
"""

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def test_grammar_changes():
    parser = DanaParser()

    tests = [
        # Test 1: Existing code should still work
        ("Basic assignment", "x = 42"),
        ("Function definition", "def test():\n    pass"),
        ("Function with params", "def test(x, y):\n    return x + y"),
        ("Scoped assignment", 'private:data = {"key": "value"}'),
        # Test 2: New typed assignments should work
        ("Typed assignment int", "x: int = 42"),
        ("Typed assignment str", 'name: str = "Alice"'),
        ("Typed assignment list", "items: list = [1, 2, 3]"),
        ("Typed assignment dict", 'config: dict = {"debug": true}'),
        # Test 3: New typed functions should work
        ("Typed function params", "def test(x: int, y: str):\n    pass"),
        ("Typed function return", "def test() -> int:\n    return 42"),
        ("Typed function full", 'def test(x: int, y: str) -> dict:\n    return {"x": x, "y": y}'),
        # Test 4: Mixed typed/untyped should work
        ("Mixed params", "def test(x: int, y):\n    pass"),
        ("Mixed assignments", 'x: int = 42\ny = "hello"'),
    ]

    passed = 0
    failed = 0

    for test_name, code in tests:
        try:
            result = parser.parse(code, do_transform=False)
            print(f"✅ {test_name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = test_grammar_changes()
    exit(0 if success else 1)
