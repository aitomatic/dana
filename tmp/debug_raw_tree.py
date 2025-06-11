#!/usr/bin/env python3

from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from lark import Token, Tree

# Test complete decorated function
code = """
@poet
def simple_func() -> str:
    return "hello"
"""

print(f"Testing: {repr(code)}")
try:
    parser = DanaParser()

    # Get raw parse tree (before transformation)
    raw_tree = parser.parser.parse(code)
    print("Raw parse tree:")
    print(raw_tree.pretty())

    # Now transform it
    ast = parser.parse(code)
    print("\nTransformed AST:", ast)

except Exception as e:
    print("FAILED:", e)
    import traceback

    traceback.print_exc()
