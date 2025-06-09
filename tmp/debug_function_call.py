#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")
os.environ["DANAPATH"] = "/Users/ctn/src/aitomatic/opendxa/tests/dana/sandbox/interpreter/test_modules"

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def debug_function_call():
    print("=== Function Import and Call Debug ===")

    sandbox = DanaSandbox()

    # Step 1: Import the function
    print("1. Importing function...")
    result = sandbox.eval("from utils.numbers import factorial")
    print(f"   Import success: {result.success}")

    if not result.success:
        print(f"   Import error: {result.error}")
        return

    # Step 2: Check what's in the context
    print("2. Checking context...")
    local_scope = result.final_context.get_scope("local")
    factorial_obj = local_scope.get("factorial")
    print(f"   Factorial object type: {type(factorial_obj)}")
    print(f"   Factorial callable: {callable(factorial_obj)}")

    # Step 3: Check function registry
    print("3. Checking function registry...")
    registry = sandbox._interpreter.function_registry
    print(f"   Registry has 'factorial' in local: {registry.has('factorial', 'local')}")

    # Step 4: Try different ways of calling
    print("4. Testing function calls...")

    # Method 1: Direct call through sandbox
    print("   Method 1: sandbox.eval('factorial(4)')")
    call_result = sandbox.eval("factorial(4)")
    print(f"   Success: {call_result.success}")
    if not call_result.success:
        print(f"   Error: {call_result.error}")
    else:
        print(f"   Result: {call_result.result}")

    # Method 2: Direct function call
    print("   Method 2: Direct function call")
    try:
        from opendxa.dana.sandbox.sandbox_context import SandboxContext

        ctx = SandboxContext()
        direct_result = factorial_obj(ctx, 4)
        print(f"   Direct call result: {direct_result}")
    except Exception as e:
        print(f"   Direct call error: {e}")

    # Method 3: Registry call
    print("   Method 3: Registry call")
    try:
        ctx = SandboxContext()
        registry_result = registry.call("factorial", ctx, "local", 4)
        print(f"   Registry call result: {registry_result}")
    except Exception as e:
        print(f"   Registry call error: {e}")


if __name__ == "__main__":
    debug_function_call()
