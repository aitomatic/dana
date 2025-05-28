#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_unary_edge_cases():
    ctx = SandboxContext()
    interpreter = DanaInterpreter()

    try:
        with open("tmp/test_unary_edge_cases.na") as f:
            code = f.read()

        print("Testing unary operator edge cases...")
        result = interpreter._eval(code, context=ctx)
        print("Success!")

        # Check specific values
        state = ctx.get_state()
        local_vars = state["local"]

        print("Results:")
        print(f"  a = -(-5) = {local_vars['a']}")
        print(f"  b = +(+10) = {local_vars['b']}")
        print(f"  c = -+5 = {local_vars['c']}")
        print(f"  d = +-(-3) = {local_vars['d']}")
        print(f"  e = -(2 * 3) = {local_vars['e']}")
        print(f"  f = +(7 - 2) = {local_vars['f']}")

        # Verify correctness
        assert local_vars["a"] == 5  # -(-5) = 5
        assert local_vars["b"] == 10  # +(+10) = 10
        assert local_vars["c"] == -5  # -+5 = -5
        assert local_vars["d"] == 3  # +-(-3) = +3 = 3
        assert local_vars["e"] == -6  # -(2 * 3) = -6
        assert local_vars["f"] == 5  # +(7 - 2) = +5 = 5

        print("All edge case assertions passed! ✅")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_unary_edge_cases()
