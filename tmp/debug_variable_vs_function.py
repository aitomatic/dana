#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")
os.environ["DANAPATH"] = "/Users/ctn/src/aitomatic/opendxa/tests/dana/sandbox/interpreter/test_modules"

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def debug_variable_vs_function():
    print("=== Debugging Variable vs Function Access ===")

    sandbox = DanaSandbox()

    # Import the function
    result1 = sandbox.eval("from utils import get_package_info")
    print(f"1. Import success: {result1.success}")

    # Test variable access (should return DanaFunction object)
    result2 = sandbox.eval("get_package_info")
    print(f"2. Variable access: {result2.success}")
    print(f"   Type: {type(result2.result)}")
    print(f"   Result: {result2.result}")

    # Test function call (should execute the function)
    result3 = sandbox.eval("get_package_info()")
    print(f"3. Function call: {result3.success}")
    print(f"   Type: {type(result3.result)}")
    print(f"   Result: {result3.result}")

    # Let's see what's in the context
    if result1.success and result1.final_context:
        try:
            context = result1.final_context
            local_vars = context.state.get("local", {})
            print(f"4. Context variables: {list(local_vars.keys())}")
            if "get_package_info" in local_vars:
                func_obj = local_vars["get_package_info"]
                print(f"   get_package_info type: {type(func_obj)}")
                print(f"   callable: {callable(func_obj)}")
        except Exception as e:
            print(f"4. Error inspecting context: {e}")

    # Test that working dotted access for comparison
    result4 = sandbox.eval("import utils")
    result5 = sandbox.eval("utils.get_package_info()")
    print(f"5. Dotted function call (working): {result5.success}")
    print(f"   Type: {type(result5.result)}")
    print(f"   Result: {result5.result}")


if __name__ == "__main__":
    debug_variable_vs_function()
