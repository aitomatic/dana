#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.dana_interpreter import DanaInterpreter
from opendxa.dana.sandbox.parser.dana_parser import DanaParser
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_deep_trace():
    """Deep trace of the error flow."""

    print("=== Deep Trace of Error Flow ===")

    # Patch multiple levels to see the flow
    from opendxa.dana.sandbox.interpreter.executor.function_executor import FunctionExecutor
    from opendxa.dana.sandbox.interpreter.functions.dana_function import DanaFunction
    from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry

    # Store original methods
    original_execute_function_call = FunctionExecutor.execute_function_call
    original_registry_call = FunctionRegistry.call
    original_registry_resolve = FunctionRegistry.resolve
    original_dana_execute = DanaFunction.execute

    def patched_execute_function_call(self, node, context):
        print(f"\n>>> FunctionExecutor.execute_function_call: {node.name}")
        try:
            result = original_execute_function_call(self, node, context)
            print(f"<<< FunctionExecutor.execute_function_call SUCCESS: {node.name}")
            return result
        except Exception as e:
            print(f"<<< FunctionExecutor.execute_function_call ERROR: {node.name} -> {e}")
            raise

    def patched_registry_call(self, name, context, namespace, *args, **kwargs):
        print(f">>> FunctionRegistry.call: {name}")
        try:
            result = original_registry_call(self, name, context, namespace, *args, **kwargs)
            print(f"<<< FunctionRegistry.call SUCCESS: {name}")
            return result
        except Exception as e:
            print(f"<<< FunctionRegistry.call ERROR: {name} -> {e}")
            raise

    def patched_registry_resolve(self, name, namespace=None):
        print(f">>> FunctionRegistry.resolve: {name} (namespace: {namespace})")
        try:
            result = original_registry_resolve(self, name, namespace)
            print(f"<<< FunctionRegistry.resolve SUCCESS: {name}")
            return result
        except Exception as e:
            print(f"<<< FunctionRegistry.resolve ERROR: {name} -> {e}")
            raise

    def patched_dana_execute(self, context, *args, **kwargs):
        print(">>> DanaFunction.execute")
        try:
            result = original_dana_execute(self, context, *args, **kwargs)
            print("<<< DanaFunction.execute SUCCESS")
            return result
        except Exception as e:
            print(f"<<< DanaFunction.execute ERROR: {e}")
            raise

    # Apply patches
    FunctionExecutor.execute_function_call = patched_execute_function_call
    FunctionRegistry.call = patched_registry_call
    FunctionRegistry.resolve = patched_registry_resolve
    DanaFunction.execute = patched_dana_execute

    try:
        interpreter = DanaInterpreter()
        context = SandboxContext()
        parser = DanaParser()

        # Simple case: function that calls sum()
        dana_code = """
def calculate_total(numbers):
    return sum(numbers)

result = calculate_total([1, 2, 3])
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
        # Restore original methods
        FunctionExecutor.execute_function_call = original_execute_function_call
        FunctionRegistry.call = original_registry_call
        FunctionRegistry.resolve = original_registry_resolve
        DanaFunction.execute = original_dana_execute


if __name__ == "__main__":
    test_deep_trace()
