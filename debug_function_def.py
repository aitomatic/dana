#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def debug_function_def():
    parser = DanaParser()

    # Simple function definition
    code = """def main():
    log_level("INFO")"""

    print("Testing simple function definition:")
    print(code)

    try:
        # Parse without transformation first to see raw parse tree
        raw_result = parser.parse(code, do_transform=False, do_type_check=False)
        print("\nRaw parse tree:")
        print(raw_result)

        # Now parse with transformation
        result = parser.parse(code, do_transform=True, do_type_check=False)
        print("\nTransformed result:")
        print(result)

        if result.statements:
            func_def = result.statements[0]
            print(f"\nFunction definition type: {type(func_def).__name__}")
            print(f"Function name: {func_def.name.name}")
            print(f"Function parameters: {func_def.parameters}")
            print(f"Function body length: {len(func_def.body)}")
            print(f"Function body: {func_def.body}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_function_def()
