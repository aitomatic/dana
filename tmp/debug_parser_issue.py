#!/usr/bin/env python3

import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def debug_parser_issue():
    print("=== Debugging Parser Function Call Detection ===")

    parser = DanaParser()

    # Test various function call patterns
    test_cases = [
        "get_package_info()",
        "factorial(4)",
        "len([1, 2, 3])",
        "print('hello')",
        "utils.get_package_info()",
        "math.sqrt(16)",
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case}")
        try:
            ast = parser.parse(test_case)
            stmt = ast.statements[0]
            print(f"   Type: {type(stmt)}")
            print(f"   Node: {stmt}")

            # Check if it's an assignment and look at the value
            if hasattr(stmt, "value"):
                print(f"   Value type: {type(stmt.value)}")
                print(f"   Value: {stmt.value}")
        except Exception as e:
            print(f"   ERROR: {e}")


if __name__ == "__main__":
    debug_parser_issue()
