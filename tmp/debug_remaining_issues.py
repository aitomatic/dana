#!/usr/bin/env python3
"""
Debug the 2 remaining failing tests:
1. Error accessing variable 'public.PACKAGE_NAME'
2. Function 'local.factorial' not found in registry
"""

import os
import sys

sys.path.insert(0, os.path.abspath("."))

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def test_package_variable_access():
    """Test 1: Debug public.PACKAGE_NAME variable access issue"""
    print("=" * 60)
    print("TEST 1: Variable Access Issue")
    print("=" * 60)

    sandbox = DanaSandbox()

    # Test the exact failing case
    code = """
from utils import get_package_info
result = get_package_info()
print(f"Result: {result}")
"""

    print("Code being executed:")
    print(code)
    print("\n" + "-" * 40)

    result = sandbox.run(code)
    print(f"Success: {result.success}")
    print(f"Result: {result.result}")
    print(f"Error: {result.error}")

    if result.final_context:
        print("\nContext state:")
        for scope, content in result.final_context.state.items():
            print(f"  {scope}: {content}")

    return result.success


def test_function_registry_issue():
    """Test 2: Debug function registry lookup issue"""
    print("\n" + "=" * 60)
    print("TEST 2: Function Registry Issue")
    print("=" * 60)

    sandbox = DanaSandbox()

    # Test the exact failing case
    code = """
from utils.numbers import factorial as fact
n = 4
result = fact(n)
print(f"factorial({n}) = {result}")
"""

    print("Code being executed:")
    print(code)
    print("\n" + "-" * 40)

    result = sandbox.run(code)
    print(f"Success: {result.success}")
    print(f"Result: {result.result}")
    print(f"Error: {result.error}")

    if result.final_context:
        print("\nContext state:")
        for scope, content in result.final_context.state.items():
            print(f"  {scope}: {content}")

    return result.success


def analyze_module_loading():
    """Analyze what happens during module loading to understand the issues"""
    print("\n" + "=" * 60)
    print("ANALYSIS: Module Loading Investigation")
    print("=" * 60)

    sandbox = DanaSandbox()

    # Step 1: Check if modules load correctly
    print("Step 1: Loading utils module...")
    result1 = sandbox.run("import utils")
    print(f"Import utils success: {result1.success}")
    if result1.error:
        print(f"Import error: {result1.error}")

    # Step 2: Check module contents
    if result1.success:
        print("\nStep 2: Checking utils module contents...")
        result2 = sandbox.run("print(dir(utils))")
        print(f"Module contents result: {result2.result}")

        # Step 3: Try direct access
        print("\nStep 3: Direct access to utils.PACKAGE_VERSION...")
        result3 = sandbox.run("print(utils.PACKAGE_VERSION)")
        print(f"Direct access success: {result3.success}")
        if result3.error:
            print(f"Direct access error: {result3.error}")


if __name__ == "__main__":
    print("Debug script for remaining Dana package import issues")
    print("Working directory:", os.getcwd())
    print("DANAPATH:", os.environ.get("DANAPATH", "Not set"))

    # Use existing DANAPATH if set correctly, don't override
    print("DANAPATH:", os.environ["DANAPATH"])

    test1_success = test_package_variable_access()
    test2_success = test_function_registry_issue()
    analyze_module_loading()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Test 1 (Variable Access): {'PASS' if test1_success else 'FAIL'}")
    print(f"Test 2 (Function Registry): {'PASS' if test2_success else 'FAIL'}")

    if test1_success and test2_success:
        print("🎉 All issues resolved!")
    else:
        print("🔧 Issues still need fixing")
