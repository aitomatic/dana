#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

# Set up environment
os.environ["DANAPATH"] = "/Users/ctn/src/aitomatic/opendxa/tests/dana/sandbox/interpreter/test_modules"

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def test_issue_3_hasattr():
    """Test Issue #3: hasattr() returns None instead of True/False"""
    print("=" * 60)
    print("ISSUE #3: hasattr() Return Value Test")
    print("=" * 60)

    sandbox = DanaSandbox()

    # Test 1: hasattr with existing attribute
    print("Test 1: hasattr with existing attribute...")
    result = sandbox.eval(
        """
obj = {"key": "value"}
result = hasattr(obj, "key")
result
"""
    )
    print(f"  Success: {result.success}")
    print(f"  Result: {result.result} (type: {type(result.result)})")
    if result.error:
        print(f"  Error: {result.error}")

    # Test 2: hasattr with missing attribute
    print("\nTest 2: hasattr with missing attribute...")
    result2 = sandbox.eval(
        """
obj = {"key": "value"}
result = hasattr(obj, "missing")
result
"""
    )
    print(f"  Success: {result2.success}")
    print(f"  Result: {result2.result} (type: {type(result2.result)})")
    if result2.error:
        print(f"  Error: {result2.error}")

    return result.success and result2.success and result.result is not None and result2.result is not None


def test_issue_4_dotted_access():
    """Test Issue #4: Dotted module access chains"""
    print("\n" + "=" * 60)
    print("ISSUE #4: Dotted Module Access Chains Test")
    print("=" * 60)

    sandbox = DanaSandbox()

    # Test 1: utils.text.function() access
    print("Test 1: utils.text.title_case() access...")
    result = sandbox.eval(
        """
import utils.text
result = utils.text.title_case('hello world')
result
"""
    )
    print(f"  Success: {result.success}")
    print(f"  Result: {result.result}")
    if result.error:
        print(f"  Error: {result.error}")

    # Test 2: Deep nesting test (if we had such modules)
    print("\nTest 2: Multiple level dotted access...")
    result2 = sandbox.eval(
        """
import utils
result = utils.PACKAGE_VERSION
result
"""
    )
    print(f"  Success: {result2.success}")
    print(f"  Result: {result2.result}")
    if result2.error:
        print(f"  Error: {result2.error}")

    return result.success and result2.success


def test_bonus_string_literal_methods():
    """Bonus Test: String literal method calls (Issue #6)"""
    print("\n" + "=" * 60)
    print("BONUS: String Literal Method Calls Test (Issue #6)")
    print("=" * 60)

    sandbox = DanaSandbox()

    # Test: "string".method() syntax
    print('Test: "hello world".split() method call...')
    result = sandbox.eval('"hello world".split()')
    print(f"  Success: {result.success}")
    print(f"  Result: {result.result}")
    if result.error:
        print(f"  Error: {result.error}")

    return result.success


if __name__ == "__main__":
    print(f"DANAPATH: {os.environ.get('DANAPATH')}")
    print()

    issue3_ok = test_issue_3_hasattr()
    issue4_ok = test_issue_4_dotted_access()
    bonus_ok = test_bonus_string_literal_methods()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Issue #3 (hasattr): {'✅ WORKING' if issue3_ok else '❌ NEEDS FIX'}")
    print(f"Issue #4 (dotted access): {'✅ WORKING' if issue4_ok else '❌ NEEDS FIX'}")
    print(f"Bonus Issue #6 (string methods): {'✅ WORKING' if bonus_ok else '❌ NEEDS FIX'}")

    if issue3_ok and issue4_ok:
        print("\n🎉 Issues 3 & 4 are already working!")
    else:
        print("\n🔧 Some issues still need attention.")
