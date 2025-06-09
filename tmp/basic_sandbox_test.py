#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

os.environ["DANAPATH"] = "/Users/ctn/src/aitomatic/opendxa/tests/dana/sandbox/interpreter/test_modules"

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def test_basic_sandbox():
    """Test if sandbox works with basic code"""
    print("Testing basic sandbox functionality...")

    sandbox = DanaSandbox()

    # Test simple expression
    result = sandbox.run("2 + 3")
    print(f"2 + 3: Success={result.success}, Result={result.result}, Error={result.error}")

    # Test simple assignment and access
    result = sandbox.run("x = 5; x")
    print(f"x = 5; x: Success={result.success}, Result={result.result}, Error={result.error}")


def test_working_imports():
    """Test imports that we know work"""
    print("\nTesting working imports...")

    sandbox = DanaSandbox()

    # Test simple module import that should work
    result = sandbox.run("import simple_math")
    print(f"import simple_math: Success={result.success}, Error={result.error}")

    if result.success:
        result2 = sandbox.run("simple_math.add(2, 3)")
        print(f"simple_math.add(2, 3): Success={result2.success}, Result={result2.result}, Error={result2.error}")


if __name__ == "__main__":
    print(f"DANAPATH: {os.environ.get('DANAPATH')}")
    test_basic_sandbox()
    test_working_imports()
