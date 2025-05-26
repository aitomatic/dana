#!/usr/bin/env python3

from opendxa.dana.sandbox.parser.dana_parser import DanaParser


def test_comment_filtering():
    """Test that comments are properly filtered out during parsing."""

    print("=== TESTING COMMENT FILTERING ===")

    # Test for loop with comment
    for_code = """
sum = 0
for i in [1, 3, 5]: # This is a comment
    sum = sum + i
"""

    print("Code:", for_code.strip())

    parser = DanaParser()

    try:
        # Parse the code
        program = parser.parse(for_code)
        print("\nParsed successfully!")
        print(f"Program: {program}")

        # Check the for loop specifically
        for stmt in program.statements:
            if hasattr(stmt, "__class__") and "ForLoop" in str(stmt.__class__):
                print("\nForLoop details:")
                print(f"  target: {stmt.target}")
                print(f"  iterable: {stmt.iterable}")
                print(f"  body: {stmt.body}")
                print(f"  body length: {len(stmt.body)}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_comment_filtering()
