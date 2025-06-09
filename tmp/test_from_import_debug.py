#!/usr/bin/env python3

import traceback

from opendxa.dana import DanaSandbox


def test_from_import_debug():
    print("=== Testing From-Import with Alias Debug ===")

    sandbox = DanaSandbox()

    try:
        print("1. Testing: from json import dumps as json_dumps")
        result = sandbox.eval("from json import dumps as json_dumps")
        print(f"✓ Import Success: {result}")

        # Check what's in the context
        print("\n2. Context state after import:")
        final_context = result.final_context
        local_scope = final_context.get_scope("local")
        print(f"Local scope keys: {list(local_scope.keys())}")

        for key, value in local_scope.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")

        # Check function registry
        print("\n3. Function registry state:")
        if hasattr(sandbox, "_interpreter") and hasattr(sandbox._interpreter, "function_registry"):
            registry = sandbox._interpreter.function_registry
            local_functions = registry.list("local")
            print(f"Functions in local namespace: {local_functions}")

            # Check if json_dumps is registered
            has_json_dumps = registry.has("json_dumps", "local")
            print(f"Has 'json_dumps' in local namespace: {has_json_dumps}")

            # Check if dumps is registered
            has_dumps = registry.has("dumps", "local")
            print(f"Has 'dumps' in local namespace: {has_dumps}")

        print("\n4. Testing: json_dumps call")
        dumps_result = sandbox.eval('json_dumps({"hello": "world"})')
        print(f"json_dumps call result: {dumps_result}")

        if not dumps_result.success:
            print(f"Error: {dumps_result.error}")

    except Exception as e:
        print(f"✗ Failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    test_from_import_debug()
