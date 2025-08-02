#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "dana"))

from dana.core.lang.dana_sandbox import DanaSandbox


def test_function_execution():
    """Test if function execution works correctly."""

    sandbox = DanaSandbox()

    # Test 1: Simple function call
    result1 = sandbox.eval("""
def test_func():
    return 42

result = test_func()
""")
    print(f"Test 1 - Simple function: success={result1.success}, result={result1.result}")

    # Test 2: Function that should fail
    result2 = sandbox.eval("""
def failing_func():
    return None.bad_attr

result = failing_func()
""")
    print(f"Test 2 - Failing function: success={result2.success}, result={result2.result}")
    if not result2.success:
        print(f"Error: {result2.error}")

    # Test 3: Nested function call
    result3 = sandbox.eval("""
def inner_func(x):
    return x.bad_attr

def outer_func(y):
    return inner_func(y)

result = outer_func(None)
""")
    print(f"Test 3 - Nested function: success={result3.success}, result={result3.result}")
    if not result3.success:
        print(f"Error: {result3.error}")


if __name__ == "__main__":
    test_function_execution()
