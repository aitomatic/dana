#!/usr/bin/env python3

import traceback

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def debug_error_propagation():
    """Debug the exact error propagation path."""

    print("=== Debugging Error Propagation ===")

    # Create interpreter and context
    interpreter = DanaInterpreter()
    context = SandboxContext()

    # Simple test case that should fail with sum() not found
    dana_code = """
def extract_metrics(data):
    total_sales = sum(data["sales"])
    return total_sales

def format_output(metrics):
    return f"Total sales: {metrics}"

business_intelligence_pipeline = extract_metrics | format_output
test_data = {"sales": [100, 200, 300]}
result = business_intelligence_pipeline(test_data)
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
                    if "business_intelligence_pipeline" in str(stmt_e):
                        print("\n   === Digging deeper into the failing call ===")

                        # Let's manually trace what happens when we call the composed function
                        try:
                            composed_func = context.get("local.business_intelligence_pipeline")
                            print(f"   Composed function: {composed_func}")
                            print(f"   Type: {type(composed_func)}")

                            if hasattr(composed_func, "left_func") and hasattr(composed_func, "right_func"):
                                print(f"   Left function: {composed_func.left_func}")
                                print(f"   Right function: {composed_func.right_func}")

                                # Try to resolve the left function
                                try:
                                    left_resolved = composed_func._resolve_function(composed_func.left_func, context)
                                    print(f"   ✓ Left function resolved: {left_resolved}")

                                    # Try to execute the left function with test data
                                    test_data = {"sales": [100, 200, 300]}
                                    print(f"   Calling left function with: {test_data}")

                                    try:
                                        intermediate_result = left_resolved.execute(context, test_data)
                                        print(f"   ✓ Left function result: {intermediate_result}")
                                    except Exception as left_e:
                                        print(f"   ✗ Left function failed: {left_e}")
                                        print("   This is the REAL error!")

                                        # Print the traceback for the real error
                                        print("   Real error traceback:")
                                        traceback.print_exc()

                                except Exception as resolve_e:
                                    print(f"   ✗ Left function resolution failed: {resolve_e}")

                        except Exception as debug_e:
                            print(f"   ✗ Debug analysis failed: {debug_e}")

                    break

        except Exception as parse_e:
            print(f"✗ Parsing failed: {parse_e}")


if __name__ == "__main__":
    debug_error_propagation()
