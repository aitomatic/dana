#!/usr/bin/env python3

from opendxa.dana.common.exceptions import FunctionRegistryError, SandboxError
from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_structured_error_info():
    """Test the structured error information from FunctionRegistryError."""

    print("=== Testing Structured FunctionRegistryError ===")

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
    except SandboxError as e:
        print("=== STRUCTURED ERROR INFORMATION ===")
        print(f"Top-level error: {e}")
        print(f"Error type: {type(e)}")

        # Check if the cause is a FunctionRegistryError
        if e.__cause__ and isinstance(e.__cause__, FunctionRegistryError):
            fre = e.__cause__
            print("\nUnderlying FunctionRegistryError:")
            print(f"  Message: {fre.message}")
            print(f"  Function name: {fre.function_name}")
            print(f"  Namespace: {fre.namespace}")
            print(f"  Operation: {fre.operation}")
            print(f"  Error type: {type(fre)}")

        print("\nFull error chain:")
        current = e
        level = 1
        while current:
            print(f"  Level {level}: {current} (type: {type(current)})")
            current = current.__cause__
            level += 1
            if level > 5:
                break


if __name__ == "__main__":
    test_structured_error_info()
