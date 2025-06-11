#!/usr/bin/env python3

from opendxa.dana.sandbox.parser.dana_parser import DanaParser

# Test complete decorated function
code = """
@poet
def simple_func() -> str:
    return "hello"
"""

print(f"Testing: {repr(code)}")
try:
    parser = DanaParser()
    ast = parser.parse(code)
    print("SUCCESS:", ast)
    func_def = ast.statements[0]
    print("Function name:", func_def.name.name)
    print("Decorators:", func_def.decorators)
    print("Return type:", func_def.return_type)
    print("Body:", func_def.body)
except Exception as e:
    print("FAILED:", e)
    import traceback

    traceback.print_exc()
