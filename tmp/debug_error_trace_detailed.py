#!/usr/bin/env python3

import sys
import traceback

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def debug_error_flow():
    """Debug the exact point where the correct error exists before being masked."""

    print("=== Tracing Error Flow in Detail ===")

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

    # Parse the code
    from opendxa.dana.sandbox.parser.dana_parser import DanaParser

    parser = DanaParser()
    program = parser.parse(dana_code)

    # Execute each statement individually to isolate the error
    for i, stmt in enumerate(program.statements):
        print(f"\nExecuting statement {i+1}: {type(stmt).__name__}")
        try:
            result = interpreter._executor.execute(stmt, context)
            print(f"   ✓ Success: {result}")
        except Exception as stmt_e:
            print(f"   ✗ Failed: {stmt_e}")

            if "test_sum" in str(stmt_e):
                print("\n=== DETAILED ERROR FLOW ANALYSIS ===")

                # Let's manually trace the exact call stack
                try:
                    # Get the test_sum function
                    test_sum_func = context.get("test_sum")
                    print(f"1. test_sum function found: {test_sum_func}")

                    # Set up the interpreter reference
                    context._interpreter = interpreter

                    # Now let's manually execute the function and catch the exact error
                    print("2. Calling test_sum([1, 2, 3])...")

                    # This should fail with the REAL error
                    try:
                        result = test_sum_func.execute(context, [1, 2, 3])
                        print(f"   Unexpected success: {result}")
                    except Exception as real_error:
                        print(f"3. REAL ERROR CAUGHT: {real_error}")
                        print(f"   Error type: {type(real_error)}")

                        # Print the full traceback to see the exact call stack
                        print("\n4. REAL ERROR TRACEBACK:")
                        exc_type, exc_value, exc_traceback = sys.exc_info()

                        # Walk through the traceback to find the exact point
                        tb_frames = []
                        tb = exc_traceback
                        while tb is not None:
                            frame = tb.tb_frame
                            filename = frame.f_code.co_filename
                            line_no = tb.tb_lineno
                            func_name = frame.f_code.co_name

                            # Only show frames from our codebase
                            if "opendxa" in filename:
                                tb_frames.append(
                                    {
                                        "filename": filename.split("/")[-1],
                                        "function": func_name,
                                        "line": line_no,
                                        "locals": dict(frame.f_locals),
                                    }
                                )

                            tb = tb.tb_next

                        # Print the relevant frames
                        for i, frame_info in enumerate(tb_frames):
                            print(f"\n   Frame {i+1}: {frame_info['filename']}:{frame_info['line']} in {frame_info['function']}")

                            # Show key local variables
                            if "node" in frame_info["locals"]:
                                node = frame_info["locals"]["node"]
                                if hasattr(node, "name"):
                                    print(f"      node.name = {node.name}")

                            if "name" in frame_info["locals"]:
                                print(f"      name = {frame_info['locals']['name']}")

                            if "ns" in frame_info["locals"]:
                                print(f"      namespace = {frame_info['locals']['ns']}")

                        # Now let's see what happens when this error gets re-raised
                        print(f"\n5. This error ({real_error}) will now bubble up and get masked...")

                        # The error that will be shown to the user is different
                        print(f"6. But the user will see: {stmt_e}")

                        print("\n=== ANALYSIS ===")
                        print(f"CORRECT ERROR: {real_error}")
                        print(f"MASKED ERROR:  {stmt_e}")
                        print(
                            "ERROR MASKING OCCURS: When the KeyError from function_registry.resolve() gets caught by function_executor.py line 271"
                        )

                except Exception as debug_e:
                    print(f"Debug analysis failed: {debug_e}")
                    traceback.print_exc()

            break


if __name__ == "__main__":
    debug_error_flow()
