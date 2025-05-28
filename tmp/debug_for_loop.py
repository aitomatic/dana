#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_for_loop_debug():
    """Debug for loop execution."""

    print("=== DEBUGGING FOR LOOP EXECUTION ===")

    # Test 1: Simple for loop with assignment
    print("\n1. FOR LOOP WITH ASSIGNMENT:")
    for_code = """
sum = 0
for i in [1, 3, 5]:
    sum = sum + i
"""

    print("Code:", for_code.strip())

    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()

    try:
        program = parser.parse(for_code)
        print("AST:", program)
        result = interpreter.execute_program(program, context)
        print(f"Final i: {context.get('local.i')}")
        print(f"Final sum: {context.get('local.sum')}")
        print(f"Context state: {context._state}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    # Test 2: For loop with simple assignment (no arithmetic)
    print("\n2. FOR LOOP WITH SIMPLE ASSIGNMENT:")
    simple_for_code = """
last_value = 0
for i in [1, 3, 5]:
    last_value = i
"""

    print("Code:", simple_for_code.strip())

    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()

    try:
        program = parser.parse(simple_for_code)
        result = interpreter.execute_program(program, context)
        print(f"Final i: {context.get('local.i')}")
        print(f"Final last_value: {context.get('local.last_value')}")
        print(f"Context state: {context._state}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    # Test 3: Check if the iterable is being processed correctly
    print("\n3. ITERABLE TEST:")
    iterable_code = """
items = [1, 3, 5]
first_item = items[0]
"""

    print("Code:", iterable_code.strip())

    interpreter = DanaInterpreter()
    context = SandboxContext()
    parser = DanaParser()

    try:
        program = parser.parse(iterable_code)
        result = interpreter.execute_program(program, context)
        print(f"items: {context.get('local.items')}")
        print(f"first_item: {context.get('local.first_item')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_for_loop_debug()
