#!/usr/bin/env python3

from opendxa.dana.sandbox.interpreter.functions.function_registry import FunctionMetadata, FunctionRegistry
from opendxa.dana.sandbox.interpreter.functions.pythonic.function_factory import PythonicFunctionFactory
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_unsupported_registration():
    """Test registering unsupported functions specifically."""
    registry = FunctionRegistry()
    factory = PythonicFunctionFactory()

    print("=== TESTING UNSUPPORTED FUNCTION REGISTRATION ===")

    # Test registering a single unsupported function manually
    function_name = "eval"
    print(f"\nTesting registration of '{function_name}':")

    def create_unsupported_handler(name):
        def unsupported_handler(context: SandboxContext, *args, **kwargs):
            factory._raise_unsupported_error(name)

        unsupported_handler.__name__ = f"{name}_unsupported"
        return unsupported_handler

    handler = create_unsupported_handler(function_name)
    metadata = FunctionMetadata(source_file="<unsupported>")
    metadata.context_aware = True
    metadata.is_public = False
    metadata.doc = f"Unsupported function: {factory.UNSUPPORTED_FUNCTIONS[function_name]['message']}"

    print(f"  Handler created: {handler}")
    print(f"  Handler name: {handler.__name__}")
    print(f"  Metadata: {metadata}")

    # Try to register
    try:
        registry.register(
            name=function_name,
            func=handler,
            func_type="python",
            metadata=metadata,
            overwrite=False,
        )
        print("  Registration: SUCCESS")
    except Exception as e:
        print(f"  Registration: FAILED - {e}")
        import traceback

        traceback.print_exc()

    # Check if it's registered
    print(f"  has('{function_name}'): {registry.has(function_name)}")

    # Try to call it
    try:
        ctx = SandboxContext()
        result = registry.call(function_name, ctx, args=[])
        print(f"  call('{function_name}'): {result}")
    except Exception as e:
        print(f"  call('{function_name}'): FAILED - {e}")
        # This should be our custom error message
        if "not supported" in str(e):
            print("  ✅ Custom error message detected!")
        else:
            print("  ❌ Unexpected error message")


def test_full_registration():
    """Test the full registration process."""
    print("\n=== TESTING FULL REGISTRATION PROCESS ===")

    registry = FunctionRegistry()
    factory = PythonicFunctionFactory()

    print(f"Unsupported functions to register: {len(factory.UNSUPPORTED_FUNCTIONS)}")
    print(f"Examples: {list(factory.UNSUPPORTED_FUNCTIONS.keys())[:5]}")

    # Register supported built-in functions first
    for function_name in factory.FUNCTION_CONFIGS:
        wrapper = factory.create_function(function_name)
        metadata = FunctionMetadata(source_file="<built-in>")
        metadata.context_aware = True
        metadata.is_public = True
        metadata.doc = factory.FUNCTION_CONFIGS[function_name]["doc"]

        try:
            registry.register(
                name=function_name,
                func=wrapper,
                func_type="python",
                metadata=metadata,
                overwrite=False,
            )
            print(f"  Registered supported: {function_name}")
        except ValueError as e:
            print(f"  Skipped supported: {function_name} - {e}")

    # Register handlers for explicitly unsupported functions
    registered_count = 0
    skipped_count = 0

    for function_name in factory.UNSUPPORTED_FUNCTIONS:

        def create_unsupported_handler(name):
            def unsupported_handler(context: SandboxContext, *args, **kwargs):
                factory._raise_unsupported_error(name)

            unsupported_handler.__name__ = f"{name}_unsupported"
            return unsupported_handler

        handler = create_unsupported_handler(function_name)
        metadata = FunctionMetadata(source_file="<unsupported>")
        metadata.context_aware = True
        metadata.is_public = False
        metadata.doc = f"Unsupported function: {factory.UNSUPPORTED_FUNCTIONS[function_name]['message']}"

        try:
            registry.register(
                name=function_name,
                func=handler,
                func_type="python",
                metadata=metadata,
                overwrite=False,
            )
            registered_count += 1
            print(f"  Registered unsupported: {function_name}")
        except ValueError as e:
            skipped_count += 1
            print(f"  Skipped unsupported: {function_name} - {e}")

    print("\nRegistration summary:")
    print(f"  Unsupported functions registered: {registered_count}")
    print(f"  Unsupported functions skipped: {skipped_count}")

    # Test a few unsupported functions
    test_unsupported = ["eval", "open", "print"]
    for func_name in test_unsupported:
        has_result = registry.has(func_name)
        print(f"  has('{func_name}'): {has_result}")


if __name__ == "__main__":
    test_unsupported_registration()
    test_full_registration()
