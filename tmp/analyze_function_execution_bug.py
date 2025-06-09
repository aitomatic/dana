#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")
os.environ["DANAPATH"] = "/Users/ctn/src/aitomatic/opendxa/tests/dana/sandbox/interpreter/test_modules"

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def analyze_function_execution_bug():
    print("=== Analyzing Function Execution Bug ===")

    sandbox = DanaSandbox()

    # Test the exact failing case
    print("\n1. Testing the failing from-import case:")
    result1 = sandbox.eval("from utils import get_package_info")
    print(f"   from utils import get_package_info: {result1.success}")

    if result1.success:
        # Check what's actually in the context
        try:
            context = result1.final_context
            if context:
                local_scope = context.get_scope("local")
                func_obj = local_scope.state.get("get_package_info")
                print(f"   Function object type: {type(func_obj)}")
                print(f"   Function callable: {callable(func_obj)}")

                # Check function registry
                registry = sandbox._interpreter.function_registry
                print(f"   Registry has 'get_package_info': {registry.has('get_package_info', 'local')}")
            else:
                print("   No context available")

        except Exception as e:
            print(f"   Error inspecting: {e}")

    # Test calling the function
    print("\n2. Testing function call:")
    result2 = sandbox.eval("get_package_info()")
    print(f"   get_package_info(): {result2.success}")

    if not result2.success:
        print(f"   Error: {result2.error}")
    else:
        print(f"   Result: {result2.result}")
        print(f"   Result type: {type(result2.result)}")

    # Compare with working dotted access
    print("\n3. Testing working dotted access:")
    result3 = sandbox.eval("import utils")
    result4 = sandbox.eval("utils.get_package_info()")
    print(f"   utils.get_package_info(): {result4.success}")
    if result4.success:
        print(f"   Result: {result4.result}")
        print(f"   Result type: {type(result4.result)}")

    # Test another case that should work
    print("\n4. Testing direct function that should work:")
    result5 = sandbox.eval("from utils.numbers import factorial")
    result6 = sandbox.eval("factorial(4)")
    print(f"   factorial(4): {result6.success}")
    if result6.success:
        print(f"   Result: {result6.result}")
    else:
        print(f"   Error: {result6.error}")


if __name__ == "__main__":
    analyze_function_execution_bug()
