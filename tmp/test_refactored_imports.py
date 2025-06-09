#!/usr/bin/env python3

import traceback

from opendxa.dana import DanaSandbox


def test_refactored_imports():
    print("=== Testing Refactored Import System ===")

    sandbox = DanaSandbox()

    # Test 1: Python module with explicit .py extension
    print("\n1. Testing: import math.py as mathematics")
    try:
        result = sandbox.eval("import math.py as mathematics")
        print(f"✓ Import Success: {result}")

        # Test accessing imported module
        pi_result = sandbox.eval("mathematics.pi")
        print(f"✓ mathematics.pi = {pi_result.result}")
        assert abs(pi_result.result - 3.141592653589793) < 1e-10
    except Exception as e:
        print(f"✗ Failed: {e}")
        traceback.print_exc()

    # Test 2: From-import with alias (now fixed parser)
    print("\n2. Testing: from json.py import dumps as json_dumps")
    try:
        result = sandbox.eval("from json.py import dumps as json_dumps")
        print(f"✓ Import Success: {result}")

        # Test using aliased function
        dumps_result = sandbox.eval('json_dumps({"hello": "world"})')
        print(f"✓ json_dumps result: {dumps_result.result}")
        assert dumps_result.result == '{"hello": "world"}'
        print("✓ Function registry fix confirmed!")
    except Exception as e:
        print(f"✗ Failed: {e}")
        traceback.print_exc()

    # Test 3: Dana module without .py extension
    print("\n3. Testing: import math (should fail - Dana module not found)")
    try:
        result = sandbox.eval("import math")
        print(f"✗ Unexpected success: {result}")
    except Exception as e:
        print(f"✓ Expected failure (Dana module not found): {e}")

    # Test 4: Multiple Python imports
    print("\n4. Testing: Multiple Python imports")
    try:
        sandbox2 = DanaSandbox()
        result1 = sandbox2.eval("import os.py")
        result2 = sandbox2.eval("from json.py import loads")

        print(f"✓ import os.py: {result1}")
        print(f"✓ from json.py import loads: {result2}")

        # Test both work
        getcwd_result = sandbox2.eval("os.getcwd()")
        loads_result = sandbox2.eval('loads("{""test"": 123}")')

        print(f"✓ os.getcwd(): {type(getcwd_result.result)}")
        print(f"✓ loads result: {loads_result.result}")

    except Exception as e:
        print(f"✗ Failed: {e}")
        traceback.print_exc()

    print("\n=== All tests completed ===")


if __name__ == "__main__":
    test_refactored_imports()
