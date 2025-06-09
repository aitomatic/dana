#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")
os.environ["DANAPATH"] = "/Users/ctn/src/aitomatic/opendxa/tests/dana/sandbox/interpreter/test_modules"

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def debug_function_call_path():
    print("=== Debugging Function Call Path ===")

    # Patch the key methods to see what's happening
    from opendxa.dana.sandbox.interpreter.executor.function_executor import FunctionExecutor
    from opendxa.dana.sandbox.interpreter.functions.dana_function import DanaFunction
    from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry

    original_registry_call = FunctionRegistry.call
    original_dana_execute = DanaFunction.execute
    original_function_executor_call = FunctionExecutor.execute_function_call

    def debug_registry_call(self, name, context=None, namespace=None, *args, **kwargs):
        print(f">>> FunctionRegistry.call: {name} (namespace: {namespace})")
        try:
            result = original_registry_call(self, name, context, namespace, *args, **kwargs)
            print(f"<<< FunctionRegistry.call SUCCESS: {name} -> {type(result)}")
            return result
        except Exception as e:
            print(f"<<< FunctionRegistry.call ERROR: {name} -> {e}")
            raise

    def debug_dana_execute(self, context, *args, **kwargs):
        print(f">>> DanaFunction.execute with {len(args)} args")
        try:
            result = original_dana_execute(self, context, *args, **kwargs)
            print(f"<<< DanaFunction.execute SUCCESS -> {type(result)}: {result}")
            return result
        except Exception as e:
            print(f"<<< DanaFunction.execute ERROR -> {e}")
            raise

    def debug_function_executor_call(self, node, context):
        print(f">>> FunctionExecutor.execute_function_call: {node.name}")
        try:
            result = original_function_executor_call(self, node, context)
            print(f"<<< FunctionExecutor.execute_function_call SUCCESS: {node.name} -> {type(result)}: {result}")
            return result
        except Exception as e:
            print(f"<<< FunctionExecutor.execute_function_call ERROR: {node.name} -> {e}")
            raise

    # Apply patches
    FunctionRegistry.call = debug_registry_call
    DanaFunction.execute = debug_dana_execute
    FunctionExecutor.execute_function_call = debug_function_executor_call

    try:
        sandbox = DanaSandbox()

        print("\n1. Testing from-import:")
        result1 = sandbox.eval("from utils import get_package_info")
        print(f"   Import success: {result1.success}")

        print("\n2. Testing function call:")
        result2 = sandbox.eval("get_package_info()")
        print(f"   Call success: {result2.success}")
        print(f"   Result type: {type(result2.result)}")
        print(f"   Result: {result2.result}")

    finally:
        # Restore original methods
        FunctionRegistry.call = original_registry_call
        DanaFunction.execute = original_dana_execute
        FunctionExecutor.execute_function_call = original_function_executor_call


if __name__ == "__main__":
    debug_function_call_path()
