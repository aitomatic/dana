#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def debug_exact_masking_point():
    """Show the exact moment where the correct error gets masked."""

    print("=== Finding Exact Error Masking Point ===")

    # Patch the function executor to show the exact masking
    from opendxa.dana.common.exceptions import SandboxError
    from opendxa.dana.sandbox.interpreter.executor.function_executor import FunctionExecutor

    # Store the original method
    original_execute_function_call = FunctionExecutor.execute_function_call

    def patched_execute_function_call(self, node, context):
        """Patched version that shows exactly where errors get masked."""
        print(f"\n=== FUNCTION CALL: {node.name} ===")

        # Get the function registry
        registry = self.function_registry
        if not registry:
            raise SandboxError(f"No function registry available to execute function '{node.name}'")

        # Evaluate arguments (simplified for debugging)
        evaluated_args = []
        evaluated_kwargs = {}

        # Extract base function name
        func_name = node.name.split(".")[-1]

        # Check local context first
        local_ns = node.name.split(".")[0] if "." in node.name else "local"
        func_key = node.name.split(".", 1)[1] if "." in node.name else node.name
        full_key = f"{local_ns}.{func_key}"

        print(f"Looking for function: {full_key}")

        try:
            # Try to get the function from the context first
            func_data = context.get(full_key)
            if func_data is not None:
                print(f"Found in context: {func_data}")
                # Execute it (this is where nested calls happen)
                try:
                    if hasattr(func_data, "execute"):
                        print("Executing function...")
                        raw_result = func_data.execute(context, *evaluated_args, **evaluated_kwargs)
                        print(f"Function executed successfully: {raw_result}")
                        return raw_result
                except Exception as nested_e:
                    print(f"NESTED EXECUTION FAILED: {nested_e}")
                    print("This nested error will bubble up...")
                    raise nested_e
        except Exception as context_e:
            print(f"Error accessing local context: {context_e}")
            pass

        # If not found in local context, try the function registry
        print("Not found in context, trying registry...")
        try:
            print(f"Calling registry.call({node.name}, ...)")
            raw_result = registry.call(node.name, context, None, *evaluated_args, **evaluated_kwargs)
            print(f"Registry call successful: {raw_result}")
            return raw_result
        except KeyError as ke:
            print(">>> EXACT MASKING POINT <<<")
            print(f"KeyError from registry: {ke}")
            print(f"About to mask as: Function '{node.name}' not found in local context or function registry")
            print(f"THE CORRECT ERROR IS: {ke}")
            print(f"THE MASKED ERROR WILL BE: Function '{node.name}' not found in local context or function registry")

            # This is line 271 - the exact masking point!
            raise SandboxError(f"Function '{node.name}' not found in local context or function registry")
        except Exception as e:
            print(f"Other exception from registry: {e}")
            print(f"This will be re-raised as: Error calling function '{node.name}': {e}")
            raise SandboxError(f"Error calling function '{node.name}': {e}")

    # Apply the patch
    FunctionExecutor.execute_function_call = patched_execute_function_call

    try:
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

        # Execute the program
        print("Executing program...")
        try:
            result = interpreter.execute_program(program, context)
            print(f"Unexpected success: {result}")
        except Exception as e:
            print("\n=== FINAL RESULT ===")
            print(f"User sees: {e}")

    finally:
        # Restore the original method
        FunctionExecutor.execute_function_call = original_execute_function_call


if __name__ == "__main__":
    debug_exact_masking_point()
