#!/usr/bin/env python3
"""
Test our unified function composition implementation.
"""

from opendxa.dana.exec.repl.repl import REPL


def test_our_implementation():
    """Test our unified function composition implementation."""

    repl = REPL()

    print("=== Testing Our Unified Function Composition ===")

    # Test 1: Basic function composition
    print("\n1. Basic Function Composition:")
    code1 = """
def add_ten(x):
    return x + 10


def double(x):
    return x * 2


math_pipeline = add_ten | double

result1 = math_pipeline(5)
print("math_pipeline(5) = " + str(result1))

result2 = 7 | math_pipeline
print("7 | math_pipeline = " + str(result2))
"""
    repl.execute(code1)

    # Test 2: Triple composition
    print("\n2. Triple Function Composition:")
    code2 = """
def stringify(x):
    return "Result: " + str(x)


full_pipeline = add_ten | double | stringify
result3 = full_pipeline(3)
print("full_pipeline(3) = " + str(result3))

result4 = 2 | full_pipeline
print("2 | full_pipeline = " + str(result4))
"""
    repl.execute(code2)

    print("\n=== All tests completed successfully! ===")


if __name__ == "__main__":
    test_our_implementation()
