#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_function_storage():
    """Test how functions are stored and retrieved."""

    print("=== Testing Function Storage ===")

    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()

    # Define a function
    dana_code = """
def test_function(data):
    return sum(data)
"""

    print("1. Defining function...")
    program = parser.parse(dana_code)
    interpreter.execute_program(program, context)

    # Check what's in the context
    print("2. Checking context contents...")
    print(f"Context keys: {list(context._state.keys())}")

    # Try to get the function
    try:
        func = context.get("test_function")
        print(f"Found 'test_function': {func}")
    except Exception as e:
        print(f"Error getting 'test_function': {e}")

    try:
        func = context.get("local.test_function")
        print(f"Found 'local.test_function': {func}")
    except Exception as e:
        print(f"Error getting 'local.test_function': {e}")

    # Now try to call it
    print("\n3. Trying to call the function...")
    call_code = """
result = test_function([1, 2, 3])
"""

    try:
        call_program = parser.parse(call_code)
        result = interpreter.execute_program(call_program, context)
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error calling function: {e}")

        # Show the error chain
        print("\n=== ERROR CHAIN ===")
        current = e
        level = 1
        while current:
            print(f"Level {level}: {current}")
            current = current.__cause__
            level += 1
            if level > 5:
                break


if __name__ == "__main__":
    test_function_storage()
