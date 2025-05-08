"""Test script for DANA REPL's Print functionality."""

import asyncio

from opendxa.dana.runtime.interpreter import LogLevel
from opendxa.dana.runtime.repl import REPL


async def test_repl_print():
    """Test the Print functionality in the REPL."""
    print("\n=== Testing DANA REPL Print Functionality ===\n")

    # Initialize REPL
    repl = REPL(log_level=LogLevel.INFO)

    # Test 1: Variable assignment
    print("\nTest 1: Variable assignment")
    result = await repl.execute("private.a = 10 + 5")
    print(f"Returned value: {result}")

    # Test 2: Expression evaluation (using print statement)
    print("\nTest 2: Expression evaluation (using print statement)")
    result = await repl.execute("print(10 * 3)")
    print(f"Returned value: {result}")

    # Test 3: Variable lookup
    print("\nTest 3: Variable lookup")
    result = await repl.execute("a")  # Should look up private.a
    print(f"Returned value: {result}")

    # Test 4: Reason statement
    # This will fail without a real LLM resource, but we can test the code path
    print("\nTest 4: Reason statement (expected to fail without LLM)")
    try:
        result = await repl.execute('reason("What is 2+2?")')
        print(f"Returned value: {result}")
    except Exception as e:
        print(f"Expected error without LLM: {e}")

    # Test 5: Complex calculation
    print("\nTest 5: Complex calculation")
    result = await repl.execute("private.b = (private.a * 2) + 3")
    print(f"Returned value: {result}")
    # Use print statement for evaluation - direct identifiers aren't supported
    result = await repl.execute("print(private.b)")
    print(f"Returned value: {result}")

    # Print final context
    print("\nFinal context values:")
    ctx = repl.get_context()
    for key, value in ctx._state["private"].items():
        if not key.startswith("__"):  # Skip internal variables
            print(f"  private.{key} = {value}")

    print("\n=== Tests complete ===")


if __name__ == "__main__":
    asyncio.run(test_repl_print())
