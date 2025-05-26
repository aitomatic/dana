#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def debug_precise_error_point():
    """Find the exact point where the correct error exists before being masked."""

    print("=== Finding Precise Error Masking Point ===")

    # Patch the function executor to intercept the error
    from opendxa.dana.sandbox.interpreter.executor.function_executor import FunctionExecutor

    # Store the original method
    original_execute_function_call = FunctionExecutor.execute_function_call

    def patched_execute_function_call(self, node, context):
        """Patched version that shows exactly where errors get masked."""
        print(f"\n>>> FUNCTION CALL: {node.name}")

        try:
            # Call the original method
            return original_execute_function_call(self, node, context)
        except KeyError as ke:
            print(f">>> KeyError caught for function '{node.name}': {ke}")
            print(">>> This is the CORRECT error that will be masked!")
            print(f">>> About to re-raise as: Function '{node.name}' not found in local context or function registry")

            # Re-raise the original error to see what happens
            raise ke
        except Exception as e:
            print(f">>> Other exception for function '{node.name}': {e}")
            raise e

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
            print(f"\nFinal error seen by user: {e}")

    finally:
        # Restore the original method
        FunctionExecutor.execute_function_call = original_execute_function_call


def debug_registry_resolve():
    """Debug the exact point in function_registry.resolve where the KeyError is raised."""

    print("\n=== Debugging Function Registry Resolve ===")

    from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry

    # Patch the resolve method
    original_resolve = FunctionRegistry.resolve

    def patched_resolve(self, name, namespace=None):
        """Patched version that shows exactly where KeyError is raised."""
        print(f"\n>>> RESOLVE: name='{name}', namespace='{namespace}'")

        try:
            result = original_resolve(self, name, namespace)
            print(f">>> RESOLVE SUCCESS: {result[0]}")
            return result
        except KeyError as ke:
            print(f">>> RESOLVE FAILED: {ke}")
            print(">>> This KeyError will bubble up and get caught by function_executor.py")
            raise ke

    # Apply the patch
    FunctionRegistry.resolve = patched_resolve

    try:
        # Create interpreter and context
        interpreter = DanaInterpreter()
        context = SandboxContext()

        # Simple test case
        dana_code = """
def test_sum(data):
    return sum(data)

result = test_sum([1, 2, 3])
"""

        # Parse and execute
        from opendxa.dana.sandbox.parser.dana_parser import DanaParser

        parser = DanaParser()
        program = parser.parse(dana_code)

        try:
            result = interpreter.execute_program(program, context)
        except Exception as e:
            print(f"\nFinal error: {e}")

    finally:
        # Restore the original method
        FunctionRegistry.resolve = original_resolve


if __name__ == "__main__":
    debug_precise_error_point()
    debug_registry_resolve()
