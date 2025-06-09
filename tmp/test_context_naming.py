#!/usr/bin/env python3

from opendxa.dana import DanaSandbox


def test_context_naming():
    print("=== Testing Context Naming Fix ===")

    sandbox = DanaSandbox()

    # Test 1: import math.py (should store as 'math' in context)
    print("\n1. Testing: import math.py")
    try:
        result = sandbox.eval("import math.py")
        print(f"✓ Import Success: {result}")

        # Check context storage
        print(f"Context keys: {list(sandbox.interpreter.context.state['local'].keys())}")

        # Test accessing as math.pi (should work now)
        pi_result = sandbox.eval("math.pi")
        print(f"✓ math.pi = {pi_result.result}")
        assert abs(pi_result.result - 3.141592653589793) < 1e-10

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()

    # Test 2: import json.py as j (should store as 'j' in context)
    print("\n2. Testing: import json.py as j")
    try:
        result = sandbox.eval("import json.py as j")
        print(f"✓ Import Success: {result}")

        # Check context storage
        print(f"Context keys: {list(sandbox.interpreter.context.state['local'].keys())}")

        # Test accessing as j.dumps (should work)
        dumps_result = sandbox.eval('j.dumps({"test": 123})')
        print(f"✓ j.dumps result: {dumps_result.result}")
        assert dumps_result.result == '{"test": 123}'

    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()

    print("\n✅ Context naming fix verified!")


if __name__ == "__main__":
    test_context_naming()
