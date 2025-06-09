#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")
os.environ["DANAPATH"] = "/Users/ctn/src/aitomatic/opendxa/tests/dana/sandbox/interpreter/test_modules"

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def test_submodule_support():
    print("=== Testing Submodule Support ===")

    sandbox = DanaSandbox()

    # Test 1: Basic submodule import
    print("\n1. Basic submodule import:")
    result = sandbox.eval("import utils.text")
    print(f"   import utils.text: {result.success}")
    if not result.success:
        print(f"   Error: {result.error}")

    # Test 2: Dotted access chain
    print("\n2. Dotted access to submodule function:")
    result = sandbox.eval('utils.text.title_case("hello world")')
    print(f"   utils.text.title_case(): {result.success} -> {result.result}")
    if not result.success:
        print(f"   Error: {result.error}")

    # Test 3: Submodule with alias
    print("\n3. Submodule import with alias:")
    result = sandbox.eval("import utils.numbers as nums")
    print(f"   import utils.numbers as nums: {result.success}")
    if result.success:
        result2 = sandbox.eval("nums.factorial(4)")
        print(f"   nums.factorial(4): {result2.success} -> {result2.result}")
        if not result2.success:
            print(f"   Error: {result2.error}")

    # Test 4: From submodule import
    print("\n4. From submodule import:")
    result = sandbox.eval("from utils.text import title_case")
    print(f"   from utils.text import title_case: {result.success}")
    if result.success:
        result2 = sandbox.eval('title_case("hello world")')
        print(f"   title_case(): {result2.success} -> {result2.result}")
        if not result2.success:
            print(f"   Error: {result2.error}")
    else:
        print(f"   Error: {result.error}")

    # Test 5: From submodule import function that uses complex operations
    print("\n5. From submodule import (complex function):")
    result = sandbox.eval("from utils.text import capitalize_words")
    print(f"   from utils.text import capitalize_words: {result.success}")
    if result.success:
        result2 = sandbox.eval('capitalize_words("hello world")')
        print(f"   capitalize_words(): {result2.success} -> {result2.result}")
        if not result2.success:
            print(f"   Error: {result2.error}")


if __name__ == "__main__":
    test_submodule_support()
