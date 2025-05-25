#!/usr/bin/env python3
"""
Quick test for the new DanaSandbox API
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def test_eval_simple():
    """Test simple code evaluation."""
    print("Testing DanaSandbox.eval...")

    # Test instance method
    sandbox = DanaSandbox()
    result = sandbox.eval('x = 42\nprint("Hello World")\nx')

    print(f"Success: {result.success}")
    print(f"Result: {result.result}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error}")

    assert result.success, f"Expected success, got error: {result.error}"
    assert result.result == 42, f"Expected 42, got {result.result}"

    print("✓ DanaSandbox.eval works!")


def test_quick_eval():
    """Test quick evaluation using class method."""
    print("\nTesting DanaSandbox.quick_eval...")

    result = DanaSandbox.quick_eval("y = 100\ny * 2")

    print(f"Success: {result.success}")
    print(f"Result: {result.result}")
    print(f"Error: {result.error}")

    assert result.success, f"Expected success, got error: {result.error}"
    assert result.result == 200, f"Expected 200, got {result.result}"

    print("✓ DanaSandbox.quick_eval works!")


def test_simple_file():
    """Test running a simple Dana file."""
    print("\nTesting simple Dana file...")

    # Create a simple test file
    test_content = """# Simple test
x = 10
y = 20
result = x + y
print("Sum calculated")
result
"""

    with open("test_simple.na", "w") as f:
        f.write(test_content)

    try:
        result = DanaSandbox.quick_run("test_simple.na")

        print(f"Success: {result.success}")
        print(f"Result: {result.result}")
        print(f"Output: {result.output}")
        print(f"Error: {result.error}")

        assert result.success, f"Expected success, got error: {result.error}"
        assert result.result == 30, f"Expected 30, got {result.result}"

        print("✓ DanaSandbox.quick_run works!")

    finally:
        if os.path.exists("test_simple.na"):
            os.remove("test_simple.na")


if __name__ == "__main__":
    try:
        test_eval_simple()
        test_quick_eval()
        test_simple_file()
        print("\n🎉 All tests passed! New API works correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
