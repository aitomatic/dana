#!/usr/bin/env python3

import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def debug_string_parsing():
    print("=== Debugging String Parsing ===")

    parser = DanaParser()

    test_cases = [
        '"hello"',  # Double quotes
        "'hello'",  # Single quotes
        'capitalize_words("hello")',  # Function with double quotes
        "capitalize_words('hello')",  # Function with single quotes
        "title_case('hello world')",  # Function with single quotes and space
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case}")
        try:
            ast = parser.parse(test_case)
            stmt = ast.statements[0]
            print(f"   ✅ SUCCESS: {type(stmt)} - {stmt}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            # Print more details about the error
            if hasattr(e, "line") and hasattr(e, "column"):
                print(f"      Line {e.line}, Column {e.column}")


if __name__ == "__main__":
    debug_string_parsing()
