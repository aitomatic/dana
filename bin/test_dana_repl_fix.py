#!/usr/bin/env python3
"""Non-interactive test script to verify DANA REPL fix."""

import asyncio
import sys

from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.repl import REPL
from opendxa.dana.runtime.fixes.repl_fix import apply_repl_fix


async def test_repl_fix():
    """Run a series of tests to verify the REPL variable reference fix."""
    print("\n=== Testing DANA REPL Variable Reference Fix ===\n")
    
    # Create REPL and apply fix
    repl = REPL()
    apply_repl_fix()
    
    # Define test cases
    test_cases = [
        ("private.counter = 5", 5, "Basic assignment"),
        ("private.counter = private.counter + 1", 6, "Self-reference increment"),
        ("private.counter = private.counter * 2", 12, "Self-reference multiplication"),
        ("private.counter = private.counter - 2", 10, "Self-reference subtraction"),
        ("private.value = 100", 100, "New variable assignment"),
        ("private.result = private.counter + private.value", 110, "Multiple variable operation"),
        ("private.x = private.counter", 10, "Variable to variable copy"),
    ]
    
    # Run the tests
    all_passed = True
    for i, (code, expected, description) in enumerate(test_cases, 1):
        try:
            result = await repl.execute(code)
            matches = result == expected
            status = "✅" if matches else "❌"
            
            print(f"Test {i}: {description}")
            print(f"  Code: {code}")
            print(f"  Expected: {expected}, Got: {result} {status}\n")
            
            if not matches:
                all_passed = False
                
        except Exception as e:
            print(f"Test {i}: {description}")
            print(f"  Code: {code}")
            print(f"  ERROR: {e} ❌\n")
            all_passed = False
    
    # Show final state
    print("Final state:")
    for key, value in repl.context._state.get("private", {}).items():
        if not key.startswith("__"):
            print(f"  private.{key} = {value}")
    
    # Summary
    if all_passed:
        print("\n✅ All tests passed! Variable reference fix is working correctly.\n")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above.\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_repl_fix())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\nError running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)