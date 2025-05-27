#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionRegistry
from opendxa.dana.sandbox.interpreter.functions.pythonic.function_factory import register_pythonic_builtins


def test_registry_debug():
    """Debug the function registry to see what's actually registered."""
    registry = FunctionRegistry()

    print("=== BEFORE REGISTRATION ===")
    print(f"Registry namespaces: {list(registry._functions.keys())}")
    for ns, funcs in registry._functions.items():
        print(f"  {ns}: {list(funcs.keys())}")

    # Register built-ins
    register_pythonic_builtins(registry)

    print("\n=== AFTER REGISTRATION ===")
    print(f"Registry namespaces: {list(registry._functions.keys())}")
    for ns, funcs in registry._functions.items():
        print(f"  {ns}: {list(funcs.keys())}")

    # Test specific functions
    test_functions = ["eval", "len", "open", "print", "sum"]

    print("\n=== FUNCTION TESTS ===")
    for func_name in test_functions:
        print(f"\nTesting '{func_name}':")

        # Test has()
        has_result = registry.has(func_name)
        print(f"  has('{func_name}'): {has_result}")

        # Test resolve()
        try:
            func, func_type, metadata = registry.resolve(func_name)
            print(f"  resolve('{func_name}'): SUCCESS")
            print(f"    func: {func}")
            print(f"    type: {func_type}")
            print(f"    metadata: {metadata}")
        except Exception as e:
            print(f"  resolve('{func_name}'): FAILED - {e}")

        # Test call() with dummy context
        try:
            from opendxa.dana.sandbox.sandbox_context import SandboxContext

            ctx = SandboxContext()

            if func_name == "len":
                result = registry.call(func_name, ctx, args=[[1, 2, 3]])
                print(f"  call('{func_name}', [1,2,3]): {result}")
            elif func_name == "sum":
                result = registry.call(func_name, ctx, args=[[1, 2, 3]])
                print(f"  call('{func_name}', [1,2,3]): {result}")
            else:
                # For unsupported functions, this should raise an error
                result = registry.call(func_name, ctx, args=[])
                print(f"  call('{func_name}', []): {result}")
        except Exception as e:
            print(f"  call('{func_name}'): FAILED - {e}")


if __name__ == "__main__":
    test_registry_debug()
