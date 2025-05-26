#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_nested_function_error():
    """Test the improved error message for nested function calls."""

    print("=== Testing Nested Function Error ===")

    # Simple case: function that calls missing function
    dana_code = """
def test_function(data):
    return missing_function(data)

result = test_function([1, 2, 3])
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
        print("Before fix: Would show 'Function test_function not found'")
        print("After fix: Should show the actual missing function")


def test_sum_function_error():
    """Test the specific sum() function error."""

    print("\n=== Testing sum() Function Error ===")

    # Specific case: function that calls sum()
    dana_code = """
def calculate_total(numbers):
    return sum(numbers)

result = calculate_total([1, 2, 3])
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


if __name__ == "__main__":
    test_nested_function_error()
    test_sum_function_error()
