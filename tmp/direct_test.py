#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

# Set up environment
os.environ["DANAPATH"] = "/Users/ctn/src/aitomatic/opendxa/tests/dana/sandbox/interpreter/test_modules"

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def test_exact_failing_case_1():
    """Replicate: test_from_package_import_function"""
    print("=" * 60)
    print("EXACT TEST 1: test_from_package_import_function")
    print("=" * 60)

    sandbox = DanaSandbox()

    # This is the exact code from the failing test
    result = sandbox.run(
        """
from utils import get_package_info
result = get_package_info()
public:PACKAGE_NAME
"""
    )

    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    if result.output:
        print(f"Output: {result.output}")


def test_exact_failing_case_2():
    """Replicate: test_from_submodule_import_with_alias"""
    print("\n" + "=" * 60)
    print("EXACT TEST 2: test_from_submodule_import_with_alias")
    print("=" * 60)

    sandbox = DanaSandbox()

    # This is the exact code from the failing test
    result = sandbox.run(
        """
from utils.numbers import factorial as fact
n = 4
fact(n)
"""
    )

    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    if result.output:
        print(f"Output: {result.output}")


if __name__ == "__main__":
    print("Testing exact failing cases...")
    print(f"DANAPATH: {os.environ.get('DANAPATH')}")

    test_exact_failing_case_1()
    test_exact_failing_case_2()
