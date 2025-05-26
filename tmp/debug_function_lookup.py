#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.ast import *
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_error_handling():
    """Test the exact scenario from the failing test."""

    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Function that raises an error
    call_count = 0

    def error_func(context, x):
        nonlocal call_count
        call_count += 1
        print(f"error_func called #{call_count} with context={type(context)}, x={x}")
        if call_count == 1:
            # First call - this should work
            raise ValueError(f"Error processing {x}")
        else:
            # Second call - this shouldn't happen
            print("ERROR: error_func called a second time!")
            import traceback

            traceback.print_stack()
            raise ValueError(f"Second call error processing {x}")

    # Normal function
    def double(context, x):
        print(f"double called with context={type(context)}, x={x}")
        return x * 2

    interpreter.function_registry.register("error_func", error_func)
    interpreter.function_registry.register("double", double)

    # Debug: Check how the functions are registered
    error_func_obj, _, _ = interpreter.function_registry.resolve("error_func")
    double_func_obj, _, _ = interpreter.function_registry.resolve("double")

    print(f"error_func_obj: {type(error_func_obj)}")
    print(f"  wants_context: {error_func_obj.wants_context}")
    print(f"  context_param_name: {error_func_obj.context_param_name}")
    print(f"  parameters: {error_func_obj.parameters}")

    print(f"double_func_obj: {type(double_func_obj)}")
    print(f"  wants_context: {double_func_obj.wants_context}")
    print(f"  context_param_name: {double_func_obj.context_param_name}")
    print(f"  parameters: {double_func_obj.parameters}")
    print()

    # Create composition: f = double | error_func
    composition = BinaryExpression(left=Identifier("double"), operator=BinaryOperator.PIPE, right=Identifier("error_func"))

    program = Program([Assignment(target=Identifier("local.f"), value=composition)])

    interpreter.execute_program(program, context)

    # Test that error is propagated correctly
    composed_func = context.get("local.f")
    print(f"Composed function type: {type(composed_func)}")

    try:
        print("Calling composed_func(context, 5)...")
        result = composed_func(context, 5)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_error_handling()
