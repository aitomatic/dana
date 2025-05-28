#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_context_exception():
    """Test what exception is thrown when executing function from context."""

    print("=== Testing Context Exception ===")

    # Patch the function executor to see the exception
    from opendxa.dana.sandbox.interpreter.executor.function_executor import FunctionExecutor
    from opendxa.dana.sandbox.interpreter.functions.sandbox_function import SandboxFunction

    # Store the original method
    original_execute_function_call = FunctionExecutor.execute_function_call

    def patched_execute_function_call(self, node, context):
        """Patched version that shows the context exception."""
        print(f"\n=== FUNCTION CALL: {node.name} ===")

        # Get the function registry
        registry = self.function_registry
        if not registry:
            raise SandboxError(f"No function registry available to execute function '{node.name}'")

        # Evaluate arguments (simplified)
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
                print(f"Type: {type(func_data)}")
                print(f"Is SandboxFunction: {isinstance(func_data, SandboxFunction)}")

                # Check if it's a SandboxFunction
                if isinstance(func_data, SandboxFunction):
                    print("Executing as SandboxFunction...")
                    try:
                        raw_result = func_data.execute(context, *evaluated_args, **evaluated_kwargs)
                        print(f"Success: {raw_result}")
                        return raw_result
                    except Exception as exec_e:
                        print(f"EXECUTION EXCEPTION: {exec_e}")
                        print(f"Exception type: {type(exec_e)}")
                        raise exec_e
                else:
                    print("Not a SandboxFunction, checking other types...")

        except Exception as context_e:
            print(f"CONTEXT EXCEPTION: {context_e}")
            print(f"Exception type: {type(context_e)}")
            print("This exception will cause fallback to registry...")
            # Continue to registry lookup
            pass

        # If not found in local context, try the function registry
        print("Falling back to registry...")
        try:
            raw_result = registry.call(node.name, context, None, *evaluated_args, **evaluated_kwargs)
            print(f"Registry success: {raw_result}")
            return raw_result
        except Exception as registry_e:
            print(f"REGISTRY EXCEPTION: {registry_e}")
            raise registry_e

    # Apply the patch
    FunctionExecutor.execute_function_call = patched_execute_function_call

    try:
        interpreter = DanaInterpreter()
        context = SandboxContext()
        parser = DanaParser()

        # Define and call a function
        dana_code = """
def test_function(data):
    return sum(data)

result = test_function([1, 2, 3])
"""

        print("Dana code:")
        print(dana_code)
        print()

        try:
            program = parser.parse(dana_code)
            result = interpreter.execute_program(program, context)
            print(f"Final success: {result}")
        except Exception as e:
            print(f"Final error: {e}")

    finally:
        # Restore the original method
        FunctionExecutor.execute_function_call = original_execute_function_call


if __name__ == "__main__":
    test_context_exception()
