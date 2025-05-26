#!/usr/bin/env python3

import inspect

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def debug_call_stack():
    """Debug the call stack to understand the frame structure."""

    # Patch the function registry to show detailed stack info
    from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry

    original_get_calling_function_context = FunctionRegistry._get_calling_function_context

    def debug_get_calling_function_context(self):
        """Debug version that shows all frames."""
        print("\n=== CALL STACK FRAMES DEBUG ===")

        for i, frame_info in enumerate(inspect.stack()):
            frame = frame_info.frame
            print(f"Frame {i}: {frame_info.filename}:{frame_info.lineno} in {frame_info.function}")

            if "self" in frame.f_locals:
                obj = frame.f_locals["self"]
                print(f"  self type: {type(obj)}")

                if hasattr(obj, "__class__"):
                    class_name = str(obj.__class__)
                    print(f"  class: {class_name}")

                    if "FunctionExecutor" in class_name:
                        if "node" in frame.f_locals:
                            node = frame.f_locals["node"]
                            if hasattr(node, "name"):
                                print(f"  FunctionExecutor node: {node.name}")

                    elif "DanaFunction" in class_name:
                        print("  DanaFunction found!")
                        print(f"  DanaFunction object: {obj}")
                        print(f"  DanaFunction attributes: {[attr for attr in dir(obj) if not attr.startswith('_')]}")
                        if hasattr(obj, "parameters"):
                            print(f"  DanaFunction parameters: {obj.parameters}")

                        # Look at all frame locals
                        print(f"  Frame locals: {list(frame.f_locals.keys())}")

                        if "context" in frame.f_locals:
                            ctx = frame.f_locals["context"]
                            print(f"  context type: {type(ctx)}")
                            if hasattr(ctx, "_state"):
                                print(f"  context state keys: {list(ctx._state.keys())}")
                                # Look at the local scope specifically
                                if "local" in ctx._state:
                                    local_scope = ctx._state["local"]
                                    print(f"  local scope type: {type(local_scope)}")
                                    print(f"  local scope keys: {list(local_scope.keys()) if hasattr(local_scope, 'keys') else 'no keys'}")
                                    if hasattr(local_scope, "keys"):
                                        for key, value in local_scope.items():
                                            if value is obj:
                                                print(f"  Found DanaFunction name: {key}")

            print()

        print("=== END CALL STACK DEBUG ===\n")

        # Call original function
        return original_get_calling_function_context(self)

    # Apply patch
    FunctionRegistry._get_calling_function_context = debug_get_calling_function_context

    try:
        print("Testing pipeline call with debug info:")

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

        interpreter = DanaInterpreter()
        context = SandboxContext()
        parser = DanaParser()

        try:
            program = parser.parse(dana_code)
            result = interpreter.execute_program(program, context)
            print(f"Success: {result}")
        except Exception as e:
            print(f"Error: {e}")

    finally:
        # Restore original function
        FunctionRegistry._get_calling_function_context = original_get_calling_function_context


if __name__ == "__main__":
    debug_call_stack()
