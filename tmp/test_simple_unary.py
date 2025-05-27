#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_simple_unary():
    ctx = SandboxContext()
    interpreter = DanaInterpreter()

    try:
        with open("tmp/simple_unary_test.na") as f:
            code = f.read()

        print(f"Testing: {code.strip()}")
        result = interpreter._eval(code, context=ctx)
        print("Success!")
        print(f"Context: {ctx.get_state()}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_simple_unary()
