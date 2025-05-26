#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def test_function_def():
    parser = DanaParser()

    # Test the combined_program sample
    code = """
def main():
    log_level("INFO")
    for user in users:
        if user.is_active:
            try:
                process(user)
                log_level("DEBUG")
            except (ProcessError):
                log("failed to process user", "ERROR")
"""
    print("Testing function definition:")
    print(code)

    try:
        result = parser.parse(code, do_transform=True, do_type_check=False)
        print("Parsed successfully")

        if result.statements:
            func_def = result.statements[0]
            print(f"Function definition type: {type(func_def).__name__}")
            print(f"Function name: {func_def.name.name}")
            print(f"Function parameters: {func_def.parameters}")
            print(f"Function body length: {len(func_def.body)}")

            if func_def.body:
                for i, stmt in enumerate(func_def.body):
                    print(f"  Body statement {i}: {type(stmt).__name__}")
                    if hasattr(stmt, "name"):
                        print(f"    Name: {stmt.name}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_function_def()
