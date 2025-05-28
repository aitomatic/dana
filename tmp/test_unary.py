#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_unary_operators():
    ctx = SandboxContext()
    interpreter = DanaInterpreter()

    try:
        with open("tmp/test_unary_operators.na") as f:
            code = f.read()

        print("Testing unary operators in Dana...")
        print("Code to execute:")
        print(code)
        print("\n" + "=" * 50)
        print("Execution result:")
        result = interpreter._eval(code, context=ctx)
        print("Success!")
        print(f"Final context: {ctx.get_state()}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_unary_operators()
