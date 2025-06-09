#!/usr/bin/env python3
"""
Simple debug for the 2 remaining failing tests
"""

import os
import sys

sys.path.insert(0, os.path.abspath("."))

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def test_issue_1():
    """Test: Error accessing variable 'public.PACKAGE_NAME'"""
    print("TEST 1: Variable Access Issue")
    print("-" * 40)

    sandbox = DanaSandbox()

    code = """
from utils import get_package_info
result = get_package_info()
print(f"Result: {result}")
"""

    print("Executing:")
    print(code.strip())

    result = sandbox.run(code)
    print(f"\nSuccess: {result.success}")
    if result.error:
        print(f"Error: {result.error}")
    print()


def test_issue_2():
    """Test: Function 'local.factorial' not found in registry"""
    print("TEST 2: Function Registry Issue")
    print("-" * 40)

    sandbox = DanaSandbox()

    code = """
from utils.numbers import factorial as fact
n = 4
result = fact(n)
print(f"factorial({n}) = {result}")
"""

    print("Executing:")
    print(code.strip())

    result = sandbox.run(code)
    print(f"\nSuccess: {result.success}")
    if result.error:
        print(f"Error: {result.error}")
    print()


if __name__ == "__main__":
    print("DANAPATH:", os.environ.get("DANAPATH", "Not set"))
    print()

    test_issue_1()
    test_issue_2()
