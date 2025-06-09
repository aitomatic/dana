#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, "/Users/ctn/src/aitomatic/opendxa")

# Set up environment
os.environ["DANAPATH"] = "/Users/ctn/src/aitomatic/opendxa/tests/dana/sandbox/interpreter/test_modules"

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def analyze_get_package_info_issue():
    """Analyze the get_package_info function execution issue in detail"""
    print("=" * 60)
    print("DEEP ANALYSIS: get_package_info execution issue")
    print("=" * 60)

    sandbox = DanaSandbox()

    # Step 1: Import and examine the function
    print("Step 1: Import and examine get_package_info...")
    result = sandbox.eval("from utils import get_package_info")
    print(f"  Import success: {result.success}")

    if not result.success:
        print(f"  Import error: {result.error}")
        return

    # Step 2: Check the function context
    print("\nStep 2: Check function context...")
    get_package_info_obj = result.final_context.get("local.get_package_info")
    print(f"  Function type: {type(get_package_info_obj)}")
    print(f"  Function context: {get_package_info_obj.context if hasattr(get_package_info_obj, 'context') else 'No context'}")

    # Step 3: Try to inspect the function's stored context
    if hasattr(get_package_info_obj, "context") and get_package_info_obj.context:
        func_context = get_package_info_obj.context
        print(f"  Function's stored context has public scope: {func_context.has_scope('public')}")
        if func_context.has_scope("public"):
            public_scope = func_context.get_scope("public")
            print(f"  Public scope contents: {public_scope}")
            print(f"  PACKAGE_NAME in function context: {'PACKAGE_NAME' in public_scope}")
            print(f"  PACKAGE_VERSION in function context: {'PACKAGE_VERSION' in public_scope}")

    # Step 4: Check current execution context
    print("\nStep 4: Check current execution context...")
    current_context = result.final_context
    print(f"  Current context has public scope: {current_context.has_scope('public')}")
    if current_context.has_scope("public"):
        current_public = current_context.get_scope("public")
        print(f"  Current public scope: {current_public}")


def analyze_factorial_issue():
    """Analyze the factorial function registry issue in detail"""
    print("\n" + "=" * 60)
    print("DEEP ANALYSIS: factorial function registry issue")
    print("=" * 60)

    sandbox = DanaSandbox()

    # Step 1: Import factorial with alias
    print("Step 1: Import factorial as fact...")
    result = sandbox.eval("from utils.numbers import factorial as fact")
    print(f"  Import success: {result.success}")

    if not result.success:
        print(f"  Import error: {result.error}")
        return

    # Step 2: Check context storage
    print("\nStep 2: Check context storage...")
    final_context = result.final_context
    fact_obj = final_context.get("local.fact")
    print(f"  Function stored as 'fact': {type(fact_obj)}")

    # Also check if it was stored under 'factorial'
    try:
        factorial_obj = final_context.get("local.factorial")
        print(f"  Function stored as 'factorial': {type(factorial_obj)}")
    except:
        print("  No function stored as 'factorial'")

    # Step 3: Check function registry
    print("\nStep 3: Check function registry...")
    registry = sandbox._interpreter.function_registry
    print(f"  Registry has 'fact' in local: {registry.has('fact', 'local')}")
    print(f"  Registry has 'factorial' in local: {registry.has('factorial', 'local')}")

    # Step 4: Manual resolution test
    print("\nStep 4: Manual function resolution test...")
    from opendxa.dana.sandbox.interpreter.executor.function_executor import FunctionNameInfo
    from opendxa.dana.sandbox.parser.ast import FunctionCall, Identifier

    # Create a mock function call node to test resolution
    mock_call = FunctionCall(name=Identifier("fact"), args={"0": Identifier("n")})
    name_info = FunctionNameInfo.from_node(mock_call)
    print(
        f"  Name info: original='{name_info.original_name}', func='{name_info.func_name}', namespace='{name_info.namespace}', full_key='{name_info.full_key}'"
    )

    # Try resolution via function resolver
    resolver = sandbox._interpreter._executor.function_executor.function_resolver
    resolved = resolver.resolve_function(name_info, final_context, registry)
    print(f"  Resolved function: {resolved}")
    if resolved:
        print(f"    Type: {resolved.func_type}, Source: {resolved.source}")


if __name__ == "__main__":
    print(f"DANAPATH: {os.environ.get('DANAPATH')}")
    print()

    analyze_get_package_info_issue()
    analyze_factorial_issue()
