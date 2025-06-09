#!/usr/bin/env python3

import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def test_simple_python_submodules():
    print("=== Testing Simple Python Submodule Support ===")

    sandbox = DanaSandbox()

    # Test 1: os.path - common Python submodule
    print("\n1. os.path submodule:")
    result = sandbox.eval("import os.path.py")
    print(f"   import os.path.py: {result.success}")
    if result.success:
        # Test simple function call
        result2 = sandbox.eval('os.path.exists("/")')
        print(f"   os.path.exists('/'): {result2.success} -> {result2.result}")

        # Test another function
        result3 = sandbox.eval('os.path.join("usr", "local", "bin")')
        print(f"   os.path.join(): {result3.success} -> {result3.result}")

    # Test 2: from os.path import
    print("\n2. From os.path import:")
    result = sandbox.eval("from os.path.py import exists, join")
    print(f"   from os.path.py import exists, join: {result.success}")
    if result.success:
        result2 = sandbox.eval('exists("/")')
        print(f"   exists('/'): {result2.success} -> {result2.result}")

        result3 = sandbox.eval('join("usr", "local")')
        print(f"   join(): {result3.success} -> {result3.result}")
    else:
        print(f"   Error: {result.error}")

    # Test 3: Check what's actually in the os.path context
    print("\n3. Debugging os.path context:")
    result = sandbox.eval("import os.path.py")
    if result.success and result.final_context:
        try:
            context = result.final_context
            local_scope = context.get_scope("local")
            if "os" in local_scope.state:
                print(f"   'os' object type: {type(local_scope.state['os'])}")
                print(f"   'os' object attributes: {dir(local_scope.state['os'])[:10]}...")  # First 10 attrs
            else:
                print("   'os' not found in local scope")
        except Exception as e:
            print(f"   Error inspecting context: {e}")
    else:
        print("   No context available")

    # Test 4: Alternative - try json (has no submodules, simpler)
    print("\n4. Control test - json module (no submodules):")
    result = sandbox.eval("import json.py")
    print(f"   import json.py: {result.success}")
    if result.success:
        result2 = sandbox.eval('json.dumps({"key": "value"})')
        print(f"   json.dumps(): {result2.success} -> {result2.result}")


if __name__ == "__main__":
    test_simple_python_submodules()
