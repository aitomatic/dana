#!/usr/bin/env python3
"""Advanced test script for DANA REPL variable reference fixes."""

import asyncio
import logging
import importlib
import sys
from functools import wraps

# Configure logging for debugging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_repl_integration():
    """Test the integration of the REPL fix more directly."""
    from opendxa.dana.runtime.repl import REPL
    from opendxa.dana.runtime.fixes.repl_fix import apply_repl_fix

    # Create a REPL with the fix applied
    repl = REPL()
    apply_repl_fix()

    # Test cases
    test_cases = [
        # Basic assignment
        ("private.a = 1", 1),
        # Self-reference with addition
        ("private.a = private.a + 1", 2),
        # Self-reference with multiplication
        ("private.a = private.a * 2", 4),
        # Self-reference with subtraction
        ("private.a = private.a - 1", 3),
        # New variable
        ("private.b = 10", 10),
        # Variable to variable
        ("private.c = private.b", 10),
        # Complex expression
        ("private.result = private.a + private.b", 13),
    ]

    # Run the test cases
    print("\n===== Testing REPL with Variable Reference Fix =====\n")
    for i, (code, expected) in enumerate(test_cases, 1):
        try:
            result = await repl.execute(code)
            print(f"Test {i}: {code}")
            print(f"   Result: {result} {'✅' if result == expected else '❌'}")
            # Print current state for debugging
            print(f"   State: {repl.context._state.get('private', {})}\n")
        except Exception as e:
            print(f"Test {i}: {code}")
            print(f"   Error: {e} ❌\n")

    # Test compound operations (should be supported in the future)
    print("\n===== Testing Advanced Operations =====\n")
    compound_tests = [
        "private.counter = 1",
        "private.counter = private.counter + 1",  # Simple increment
        "private.x = 5",
        "private.y = 10",
        "private.z = private.x + private.y",     # Variable combination
    ]

    for i, code in enumerate(compound_tests, 1):
        try:
            result = await repl.execute(code)
            print(f"Advanced Test {i}: {code}")
            print(f"   Result: {result} ✅")
        except Exception as e:
            print(f"Advanced Test {i}: {code}")
            print(f"   Error: {e} ❌")

    # Show final state
    print("\nFinal State:")
    for scope, values in repl.context._state.items():
        if scope in ('private', 'public', 'system'):
            print(f"\n{scope}:")
            for key, value in values.items():
                if not key.startswith('__'):  # Skip internal variables
                    print(f"   {key} = {value}")

    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_repl_integration())
        print("\n✅ All tests completed")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
