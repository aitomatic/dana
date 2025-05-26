#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_simple_missing_function():
    """Test the improved error message for a simple missing function call."""

    print("=== Testing Simple Missing Function ===")

    # Direct call to missing function
    dana_code = """
result = missing_function([1, 2, 3])
"""

    print("Dana code:")
    print(dana_code)
    print()

    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()

    try:
        program = parser.parse(dana_code)
        result = interpreter.execute_program(program, context)
        print(f"Success: {result}")
    except Exception as e:
        print("=== IMPROVED ERROR MESSAGE ===")
        print(f"Error: {e}")
        print()

        # Show the error chain
        print("=== ERROR CHAIN ===")
        current = e
        level = 1
        while current:
            print(f"Level {level}: {current}")
            current = current.__cause__
            level += 1
            if level > 5:  # Prevent infinite loops
                break

        print()
        print("=== ANALYSIS ===")
        print("This should show the correct missing function name!")


if __name__ == "__main__":
    test_simple_missing_function()
