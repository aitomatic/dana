#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_arithmetic_debug():
    """Debug basic arithmetic operations."""

    print("=== DEBUGGING ARITHMETIC OPERATIONS ===")

    # Test 1: Simple addition
    print("\n1. SIMPLE ADDITION:")
    simple_code = """
sum = 0
sum = sum + 1
sum = sum + 3
sum = sum + 5
"""

    print("Code:", simple_code.strip())

    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()

    try:
        program = parser.parse(simple_code)
        result = interpreter.execute_program(program, context)
        print(f"Final sum: {context.get('local.sum')}")
        print("Expected sum: 9")

    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Simple for loop without continue
    print("\n2. SIMPLE FOR LOOP:")
    for_code = """
sum = 0
for i in [1, 3, 5]:
    print(f"Processing i={i}, current sum={sum}")
    sum = sum + i
    print(f"After adding i={i}, sum={sum}")
"""

    print("Code:", for_code.strip())

    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()

    try:
        program = parser.parse(for_code)
        result = interpreter.execute_program(program, context)
        print(f"Final i: {context.get('local.i')}")
        print(f"Final sum: {context.get('local.sum')}")
        print("Expected sum: 9")

    except Exception as e:
        print(f"Error: {e}")

    # Test 3: Check if variables are being set correctly
    print("\n3. VARIABLE ASSIGNMENT TEST:")
    var_code = """
x = 5
y = 3
z = x + y
"""

    print("Code:", var_code.strip())

    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()

    try:
        program = parser.parse(var_code)
        result = interpreter.execute_program(program, context)
        print(f"x: {context.get('local.x')}")
        print(f"y: {context.get('local.y')}")
        print(f"z: {context.get('local.z')}")
        print("Expected z: 8")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_arithmetic_debug()
