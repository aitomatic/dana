#!/usr/bin/env python3

import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def test_grammar_parity():
    print("=== Testing Grammar Parity for Submodules ===")

    sandbox = DanaSandbox()

    # Test the exact same dotted import syntax for both
    print("\n1. Same grammar, different execution paths:")

    # Dana path (no .py extension)
    result1 = sandbox.eval("import utils.text")
    print(f"   Dana: import utils.text -> {result1.success}")

    # Python path (.py extension required)
    result2 = sandbox.eval("import os.path.py")
    print(f"   Python: import os.path.py -> {result2.success}")

    print("\n2. Same dotted access syntax for both:")

    if result1.success:
        result3 = sandbox.eval('utils.text.title_case("hello")')
        print(f"   Dana: utils.text.title_case() -> {result3.success} = {result3.result}")

    if result2.success:
        result4 = sandbox.eval('os.path.exists("/")')
        print(f"   Python: os.path.exists() -> {result4.success} = {result4.result}")

    print("\n3. Testing if grammar is actually identical:")

    # Both should parse the same way - let's test some edge cases
    test_cases = [
        "import a.b.c",  # Dana path
        "import a.b.c.py",  # Python path
        "from x.y import z",  # Dana from-import
        "from x.y.py import z",  # Python from-import
    ]

    for case in test_cases:
        try:
            result = sandbox.eval(case)
            print(f"   '{case}' -> Parsed: ✅, Executed: {'✅' if result.success else '❌'}")
            if not result.success:
                print(f"      Error: {str(result.error)[:80]}...")
        except Exception as e:
            print(f"   '{case}' -> Parsed: ❌, Error: {str(e)[:80]}...")


if __name__ == "__main__":
    test_grammar_parity()
