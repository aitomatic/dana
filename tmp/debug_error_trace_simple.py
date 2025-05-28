#!/usr/bin/env python3

import traceback

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def debug_sum_error():
    """Debug the exact error propagation path for sum() function."""

    print("=== Debugging sum() Error Propagation ===")

    # Create interpreter and context
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Simple test case that should fail with sum() not found
    dana_code = """
def test_sum(data):
    return sum(data)

result = test_sum([1, 2, 3])
"""

    print("Dana code:")
    print(dana_code)
    print()

    try:
        # Parse the code
        print("1. Parsing...")
        from opendxa.dana.sandbox.parser.dana_parser import DanaParser

        parser = DanaParser()
        program = parser.parse(dana_code)
        print("   ✓ Parsing successful")

        # Execute the code
        print("2. Executing...")
        result = interpreter.execute_program(program, context)
        print(f"   ✓ Execution successful: {result}")

    except Exception as e:
        print(f"   ✗ Execution failed: {e}")
        print()

        # Print the full traceback
        print("Full traceback:")
        traceback.print_exc()
        print()

        # Let's trace step by step what happens
        print("=== Step-by-step Analysis ===")

        try:
            # Parse first
            from opendxa.dana.sandbox.parser.dana_parser import DanaParser

            parser = DanaParser()
            program = parser.parse(dana_code)
            print("✓ Parsing successful")

            # Execute each statement individually
            for i, stmt in enumerate(program.statements):
                print(f"\nExecuting statement {i+1}: {type(stmt).__name__}")
                try:
                    result = interpreter._executor.execute(stmt, context)
                    print(f"   ✓ Success: {result}")
                except Exception as stmt_e:
                    print(f"   ✗ Failed: {stmt_e}")

                    # If this is the failing statement, let's dig deeper
                    if "test_sum" in str(stmt_e):
                        print("\n   === Digging deeper into the failing call ===")

                        # Let's manually trace what happens when we call the function
                        try:
                            test_sum_func = context.get("test_sum")
                            print(f"   Function: {test_sum_func}")
                            print(f"   Type: {type(test_sum_func)}")

                            if hasattr(test_sum_func, "body"):
                                print(f"   Function body: {test_sum_func.body}")

                                # Try to execute the function manually
                                print("   Calling function with: [1, 2, 3]")

                                try:
                                    # Set up the interpreter reference
                                    context._interpreter = interpreter
                                    intermediate_result = test_sum_func.execute(context, [1, 2, 3])
                                    print(f"   ✓ Function result: {intermediate_result}")
                                except Exception as func_e:
                                    print(f"   ✗ Function failed: {func_e}")
                                    print("   This is the REAL error!")

                                    # Print the traceback for the real error
                                    print("   Real error traceback:")
                                    traceback.print_exc()

                        except Exception as debug_e:
                            print(f"   ✗ Debug analysis failed: {debug_e}")

                    break

        except Exception as parse_e:
            print(f"✗ Parsing failed: {parse_e}")


if __name__ == "__main__":
    debug_sum_error()
