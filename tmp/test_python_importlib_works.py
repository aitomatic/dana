#!/usr/bin/env python3

import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def test_python_importlib_works():
    print("=== Testing: Python Submodules Work Great with importlib ===")

    sandbox = DanaSandbox()

    # Test various Python submodules that should work perfectly
    test_cases = [
        # Basic submodules
        ("os.path", "exists", ['"/"']),
        ("os.path", "join", ['"usr"', '"local"', '"bin"']),
        ("os.path", "basename", ['"/usr/local/bin/python"']),
        # urllib submodules
        ("urllib.parse", "urlparse", ['"https://example.com/path?q=1"']),
        ("urllib.parse", "quote", ['"hello world"']),
        ("urllib.parse", "urljoin", ['"https://example.com/"', '"page"']),
        # xml submodules
        ("xml.etree", "ElementTree", []),  # Just check if class exists
        # json (not a submodule, but for comparison)
        ("json", "dumps", ['{"key": "value"}']),
    ]

    success_count = 0
    total_count = 0

    for module, func, args in test_cases:
        total_count += 1

        print(f"\n{total_count}. Testing {module}.{func}:")

        # Import the module
        import_cmd = f"import {module}.py"
        result1 = sandbox.eval(import_cmd)
        print(f"   {import_cmd}: {result1.success}")

        if result1.success:
            # Test function call
            args_str = ", ".join(args) if args else ""
            call_cmd = f"{module}.{func}({args_str})"
            result2 = sandbox.eval(call_cmd)

            print(f"   {call_cmd}: {result2.success}")
            if result2.success:
                print(f"   Result: {result2.result} (type: {type(result2.result).__name__})")
                success_count += 1
            else:
                print(f"   Error: {result2.error}")
        else:
            print(f"   Import failed: {result1.error}")

    print("\n=== Summary ===")
    print(f"Success Rate: {success_count}/{total_count} ({100*success_count/total_count:.1f}%)")

    if success_count == total_count:
        print("🎉 Python submodules work PERFECTLY with importlib!")
    elif success_count > total_count * 0.8:
        print("✅ Python submodules work very well with importlib!")
    else:
        print("⚠️  Some issues found with Python submodule support")

    # Test the one that had issues before
    print("\n=== Re-testing the Previous Problem Case ===")
    result1 = sandbox.eval("import collections.abc.py")
    print(f"import collections.abc.py: {result1.success}")

    if result1.success:
        # Try to access a class (this was the issue before)
        result2 = sandbox.eval("type(collections.abc)")
        print(f"type(collections.abc): {result2.success} -> {result2.result}")

        # The issue was accessing Sequence class - let's see if we can check it exists
        result3 = sandbox.eval("hasattr(collections.abc, 'Sequence')")
        print(f"hasattr(collections.abc, 'Sequence'): {result3.success} -> {result3.result}")


if __name__ == "__main__":
    test_python_importlib_works()
