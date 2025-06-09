#!/usr/bin/env python3

import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def test_python_submodule_support():
    print("=== Testing Python Submodule Support ===")

    sandbox = DanaSandbox()

    # Test 1: Basic Python submodule import
    print("\n1. Python submodule import (os.path):")
    result = sandbox.eval("import os.path.py")
    print(f"   import os.path.py: {result.success}")
    if not result.success:
        print(f"   Error: {result.error}")
    else:
        # Test accessing submodule function
        result2 = sandbox.eval('os.path.basename("/usr/local/bin/python")')
        print(f"   os.path.basename(): {result2.success} -> {result2.result}")
        if not result2.success:
            print(f"   Error: {result2.error}")

    # Test 2: Collections submodule
    print("\n2. Python submodule import (collections.abc):")
    result = sandbox.eval("import collections.abc.py")
    print(f"   import collections.abc.py: {result.success}")
    if not result.success:
        print(f"   Error: {result.error}")
    else:
        # Test accessing submodule class
        result2 = sandbox.eval("isinstance([], collections.abc.Sequence)")
        print(f"   isinstance check: {result2.success} -> {result2.result}")
        if not result2.success:
            print(f"   Error: {result2.error}")

    # Test 3: From Python submodule import
    print("\n3. From Python submodule import:")
    result = sandbox.eval("from os.path.py import basename")
    print(f"   from os.path.py import basename: {result.success}")
    if result.success:
        result2 = sandbox.eval('basename("/usr/local/bin/python")')
        print(f"   basename(): {result2.success} -> {result2.result}")
        if not result2.success:
            print(f"   Error: {result2.error}")
    else:
        print(f"   Error: {result.error}")

    # Test 4: urllib.parse submodule
    print("\n4. Python submodule import (urllib.parse):")
    result = sandbox.eval("import urllib.parse.py")
    print(f"   import urllib.parse.py: {result.success}")
    if not result.success:
        print(f"   Error: {result.error}")
    else:
        result2 = sandbox.eval('urllib.parse.urlparse("https://example.com/path")')
        print(f"   urllib.parse.urlparse(): {result2.success} -> {type(result2.result)}")
        if not result2.success:
            print(f"   Error: {result2.error}")

    # Test 5: From urllib.parse import
    print("\n5. From Python submodule import (urllib.parse):")
    result = sandbox.eval("from urllib.parse.py import urlparse")
    print(f"   from urllib.parse.py import urlparse: {result.success}")
    if result.success:
        result2 = sandbox.eval('urlparse("https://example.com/path")')
        print(f"   urlparse(): {result2.success} -> {type(result2.result)}")
        if not result2.success:
            print(f"   Error: {result2.error}")
    else:
        print(f"   Error: {result.error}")

    # Test 6: Alternative syntax without .py extension (should fail for Python modules)
    print("\n6. Python submodule without .py extension (should fail):")
    result = sandbox.eval("import os.path")
    print(f"   import os.path: {result.success}")
    if not result.success:
        print(f"   Error: {result.error}")


if __name__ == "__main__":
    test_python_submodule_support()
