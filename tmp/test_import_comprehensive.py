#!/usr/bin/env python3

import traceback

from opendxa.dana import DanaSandbox


def test_comprehensive_imports():
    print("=== Comprehensive Import Tests ===")

    sandbox = DanaSandbox()

    # Test 1: Basic Python module import
    print("\n1. Testing: import math")
    try:
        result = sandbox.eval("import math")
        print(f"✓ Success: {result}")

        # Test accessing imported module
        pi_result = sandbox.eval("math.pi")
        print(f"✓ math.pi = {pi_result.result}")
        assert abs(pi_result.result - 3.141592653589793) < 1e-10
    except Exception as e:
        print(f"✗ Failed: {e}")
        traceback.print_exc()

    # Test 2: Import with alias
    print("\n2. Testing: import json as j")
    try:
        result = sandbox.eval("import json as j")
        print(f"✓ Success: {result}")

        # Test accessing aliased module
        test_result = sandbox.eval('j.dumps({"test": 123})')
        print(f"✓ j.dumps result: {test_result.result}")
        assert test_result.result == '{"test": 123}'
    except Exception as e:
        print(f"✗ Failed: {e}")
        traceback.print_exc()

    # Test 3: From-import
    print("\n3. Testing: from math import sqrt")
    try:
        # Create new sandbox to test fresh context
        sandbox2 = DanaSandbox()
        result = sandbox2.eval("from math import sqrt")
        print(f"✓ Success: {result}")

        # Test using imported function
        sqrt_result = sandbox2.eval("sqrt(16)")
        print(f"✓ sqrt(16) = {sqrt_result.result}")
        assert sqrt_result.result == 4.0
    except Exception as e:
        print(f"✗ Failed: {e}")
        traceback.print_exc()

    # Test 4: From-import with alias
    print("\n4. Testing: from json import dumps as json_dumps")
    try:
        sandbox3 = DanaSandbox()
        result = sandbox3.eval("from json import dumps as json_dumps")
        print(f"✓ Success: {result}")

        # Test using aliased function
        dumps_result = sandbox3.eval('json_dumps({"hello": "world"})')
        print(f"✓ json_dumps result: {dumps_result.result}")
        assert dumps_result.result == '{"hello": "world"}'
    except Exception as e:
        print(f"✗ Failed: {e}")
        traceback.print_exc()

    # Test 5: Python module with .py extension
    print("\n5. Testing: import os.py (explicit Python module)")
    try:
        sandbox4 = DanaSandbox()
        result = sandbox4.eval("import os.py as operating_system")
        print(f"✓ Success: {result}")

        # Test accessing the module
        getcwd_result = sandbox4.eval("operating_system.getcwd()")
        print(f"✓ operating_system.getcwd(): {getcwd_result.result}")
        assert isinstance(getcwd_result.result, str)
    except Exception as e:
        print(f"✗ Failed: {e}")
        traceback.print_exc()

    # Test 6: Module not found error
    print("\n6. Testing: import nonexistent_module (should fail)")
    try:
        sandbox5 = DanaSandbox()
        result = sandbox5.eval("import nonexistent_module")
        print(f"✗ Unexpected success: {result}")
    except Exception as e:
        print(f"✓ Expected failure: {e}")

    print("\n=== All tests completed ===")


if __name__ == "__main__":
    test_comprehensive_imports()
