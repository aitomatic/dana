#!/usr/bin/env python3

from opendxa.dana.sandbox.parser.dana_parser import DanaParser

code = """
@poet(domain="test")
def simple_func() -> str:
    return "hello"
"""

try:
    parser = DanaParser()
    ast = parser.parse(code)
    print("AST:", ast)
    print("First statement:", ast.statements[0])
    print("Decorators:", ast.statements[0].decorators)
    for i, decorator in enumerate(ast.statements[0].decorators):
        print(f"Decorator {i}:", decorator)
        print(f"  Name: {decorator.name}")
        print(f"  Args: {decorator.args}")
        print(f"  Kwargs: {decorator.kwargs}")
except Exception as e:
    print("Parse error:", e)
    import traceback

    traceback.print_exc()
