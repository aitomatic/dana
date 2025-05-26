#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))


from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def test_simple_function_call():
    parser = DanaParser()

    # Test simple function call with double quotes
    code = 'log_level("INFO")'
    print(f"Testing: {code}")

    try:
        result = parser.parse(code, do_transform=True, do_type_check=False)
        print("Parsed successfully")

        if result.statements:
            stmt = result.statements[0]
            print(f"Statement type: {type(stmt).__name__}")
            if hasattr(stmt, "name"):
                print(f"Function name: {repr(stmt.name)}")
            if hasattr(stmt, "args"):
                print(f"Function args: {stmt.args}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


def test_scoped_function_call():
    parser = DanaParser()

    # Test scoped function call with colon and double quotes
    code = 'local:log_level("INFO")'
    print(f"\nTesting: {code}")

    try:
        result = parser.parse(code, do_transform=True, do_type_check=False)
        print("Parsed successfully")

        if result.statements:
            stmt = result.statements[0]
            print(f"Statement type: {type(stmt).__name__}")
            if hasattr(stmt, "name"):
                print(f"Function name: {repr(stmt.name)}")
            if hasattr(stmt, "args"):
                print(f"Function args: {stmt.args}")

    except Exception as e:
        print(f"Error: {e}")


def test_scoped_function_call_dot():
    parser = DanaParser()

    # Test scoped function call with dot
    code = "local.log_level('INFO')"
    print(f"\nTesting: {code}")

    try:
        result = parser.parse(code, do_transform=True, do_type_check=False)
        print("Parsed successfully")

        if result.statements:
            stmt = result.statements[0]
            print(f"Statement type: {type(stmt).__name__}")
            if hasattr(stmt, "name"):
                print(f"Function name: {repr(stmt.name)}")
            if hasattr(stmt, "args"):
                print(f"Function args: {stmt.args}")

    except Exception as e:
        print(f"Error: {e}")


def test_try_block():
    parser = DanaParser()

    # Test the actual try block from the failing test
    code = """
try:
    risky()
    log_level("ERROR")
except (ErrorType):
    handle()
    log("exception occurred", "ERROR")
finally:
    cleanup()
    log_level("INFO")
"""
    print("\nTesting try block:")
    print(code)

    try:
        result = parser.parse(code, do_transform=True, do_type_check=False)
        print("Parsed successfully")

        if result.statements:
            stmt = result.statements[0]
            print(f"Statement type: {type(stmt).__name__}")
            if hasattr(stmt, "body"):
                print(f"Try body length: {len(stmt.body)}")
                if stmt.body:
                    print(f"First body statement: {type(stmt.body[0]).__name__}")
                    if hasattr(stmt.body[0], "name"):
                        print(f"First body statement name: {stmt.body[0].name}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_simple_function_call()
    test_scoped_function_call()
    test_try_block()
