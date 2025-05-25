#!/usr/bin/env python3
"""
Test the public API exposed by the dana module
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

# Test the public API
import opendxa.dana as dana


def test_public_api():
    """Test the public API functions."""
    print("Testing public API...")

    # Test the convenience run function
    print("Testing dana.run...")
    result = dana.run("test_simple.na")
    print(f"dana.run result: success={result.success}, result={result.result}")
    assert result.success
    assert result.result == 30

    # Test the convenience eval function
    print("Testing dana.eval...")
    result = dana.eval("a = 5\nb = 7\na * b")
    print(f"dana.eval result: success={result.success}, result={result.result}")
    assert result.success
    assert result.result == 35

    # Test DanaSandbox class
    print("Testing dana.DanaSandbox...")
    sandbox = dana.DanaSandbox()
    result = sandbox.eval("c = 100\nc / 4")
    print(f"DanaSandbox.eval result: success={result.success}, result={result.result}")
    assert result.success
    assert result.result == 25.0

    print("✓ All public API tests passed!")


if __name__ == "__main__":
    try:
        test_public_api()
        print("\n🎉 Public API works correctly!")
    except Exception as e:
        print(f"\n❌ Public API test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
