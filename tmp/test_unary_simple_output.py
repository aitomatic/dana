#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_unary_simple():
    ctx = SandboxContext()
    interpreter = DanaInterpreter()

    try:
        with open("tmp/test_unary_simple_output.na") as f:
            code = f.read()

        print("Testing unary operators (simple)...")
        result = interpreter._eval(code, context=ctx)
        print("Success!")

        # Check specific values
        state = ctx.get_state()
        local_vars = state["local"]

        print("Results:")
        print(f"  negative_five = {local_vars['negative_five']}")
        print(f"  positive_five = {local_vars['positive_five']}")
        print(f"  x = {local_vars['x']}")
        print(f"  negative_x = {local_vars['negative_x']}")
        print(f"  positive_x = {local_vars['positive_x']}")
        print(f"  double_negative = {local_vars['double_negative']}")
        print(f"  mixed = {local_vars['mixed']}")
        print(f"  result = {local_vars['result']}")
        print(f"  paren_result = {local_vars['paren_result']}")

        # Verify correctness
        assert local_vars["negative_five"] == -5
        assert local_vars["positive_five"] == 5
        assert local_vars["x"] == 10
        assert local_vars["negative_x"] == -10
        assert local_vars["positive_x"] == 10
        assert local_vars["double_negative"] == 10
        assert local_vars["mixed"] == -5
        assert local_vars["result"] == -2
        assert local_vars["paren_result"] == -8

        print("All assertions passed! ✅")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_unary_simple()
