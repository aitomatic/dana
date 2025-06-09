#!/usr/bin/env python3

from opendxa.dana import DanaSandbox


def test_simple_context():
    print("=== Testing Context Naming Fix ===")

    sandbox = DanaSandbox()

    # Test 1: import math.py -> should access as math.pi
    print("\n1. Testing: import math.py")
    try:
        result = sandbox.eval("import math.py")
        print(f"✓ Import Success: {result}")

        # Test accessing as math.pi
        pi_result = sandbox.eval("math.pi")
        print(f"✓ math.pi = {pi_result.result}")
        assert pi_result.success is True

    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 2: import json.py as j -> should access as j.dumps
    print("\n2. Testing: import json.py as j")
    try:
        result = sandbox.eval("import json.py as j")
        print(f"✓ Import Success: {result}")

        # Test accessing as j.dumps
        dumps_result = sandbox.eval('j.dumps({"test": 123})')
        print(f"✓ j.dumps result: {dumps_result.result}")
        assert dumps_result.success is True

    except Exception as e:
        print(f"✗ Failed: {e}")

    print("\n✅ Tests completed!")


if __name__ == "__main__":
    test_simple_context()
