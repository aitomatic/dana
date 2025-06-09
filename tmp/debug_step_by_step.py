#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

# Set up environment
os.environ["DANAPATH"] = "/Users/ctn/src/aitomatic/opendxa/tests/dana/sandbox/interpreter/test_modules"

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def analyze_issue_1():
    """Analyze issue 1: Variable access problem"""
    print("=" * 60)
    print("ISSUE 1 ANALYSIS: Variable 'public.PACKAGE_NAME' not found")
    print("=" * 60)

    sandbox = DanaSandbox()

    # Step 1: Just import utils
    print("Step 1: Import utils...")
    result1 = sandbox.eval("from utils import get_package_info")
    print(f"  Import: Success={result1.success}, Error={result1.error}")

    # Step 2: Check what get_package_info actually is
    print("\nStep 2: Check what get_package_info is...")
    result2 = sandbox.eval("type(get_package_info)")
    print(f"  Type: Success={result2.success}, Result={result2.result}, Error={result2.error}")

    # Step 3: Try to call get_package_info()
    print("\nStep 3: Try to call get_package_info()...")
    result3 = sandbox.eval("result = get_package_info()")
    print(f"  Call: Success={result3.success}, Error={result3.error}")

    # Step 4: If call worked, check what happened to result
    if result3.success:
        print("\nStep 4: Check result value...")
        result4 = sandbox.eval("result")
        print(f"  Result: Success={result4.success}, Result={result4.result}, Error={result4.error}")

    # Step 5: Try to access public:PACKAGE_NAME directly
    print("\nStep 5: Try public:PACKAGE_NAME access...")
    result5 = sandbox.eval("public:PACKAGE_NAME")
    print(f"  Direct access: Success={result5.success}, Result={result5.result}, Error={result5.error}")


def analyze_issue_2():
    """Analyze issue 2: Function registry problem"""
    print("\n" + "=" * 60)
    print("ISSUE 2 ANALYSIS: Function 'local.factorial' not found in registry")
    print("=" * 60)

    sandbox = DanaSandbox()

    # Step 1: Import with alias
    print("Step 1: Import factorial as fact...")
    result1 = sandbox.eval("from utils.numbers import factorial as fact")
    print(f"  Import: Success={result1.success}, Error={result1.error}")

    # Step 2: Check what fact actually is
    print("\nStep 2: Check what fact is...")
    result2 = sandbox.eval("type(fact)")
    print(f"  Type: Success={result2.success}, Result={result2.result}, Error={result2.error}")

    # Step 3: Try to call fact directly
    print("\nStep 3: Try to call fact(4)...")
    result3 = sandbox.eval("n = 4")
    print(f"  Set n: Success={result3.success}, Error={result3.error}")

    result4 = sandbox.eval("fact(n)")
    print(f"  Call fact(n): Success={result4.success}, Result={result4.result}, Error={result4.error}")

    # Step 4: See if we can inspect the function further
    if result1.success:
        print("\nStep 4: Check function attributes...")
        result5 = sandbox.eval("hasattr(fact, 'execute')")
        print(f"  Has execute: Success={result5.success}, Result={result5.result}, Error={result5.error}")


if __name__ == "__main__":
    print(f"DANAPATH: {os.environ.get('DANAPATH')}")
    print()

    analyze_issue_1()
    analyze_issue_2()
