#!/usr/bin/env python3

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def test_parse_tree_debug():
    """Debug the raw parse tree before transformation."""

    print("=== DEBUGGING PARSE TREE ===")

    # Test simple for loop
    for_code = """
sum = 0
for i in [1, 3, 5]: # This is a comment
    sum = sum + i
"""

    print("Code:", for_code.strip())

    parser = DanaParser()

    try:
        # Get the raw parse tree without transformation
        parse_tree = super(DanaParser, parser).parse(for_code)
        print("\nRaw parse tree:")
        print(parse_tree.pretty())

        # Now try with transformation
        print("\nTransformed AST:")
        program = parser.parse(for_code)
        print(program)

        # Check the for loop specifically
        for stmt in program.statements:
            if hasattr(stmt, "__class__") and "ForLoop" in str(stmt.__class__):
                print("\nForLoop details:")
                print(f"  target: {stmt.target}")
                print(f"  iterable: {stmt.iterable}")
                print(f"  body: {stmt.body}")
                print(f"  body length: {len(stmt.body)}")
                for i, body_stmt in enumerate(stmt.body):
                    print(f"    body[{i}]: {body_stmt} (type: {type(body_stmt)})")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_parse_tree_debug()
