"""Test script for DANA REPL without interactive prompt."""

import asyncio
from opendxa.dana.runtime.repl import REPL
from opendxa.dana.runtime.interpreter import LogLevel

async def test_repl():
    # Initialize REPL without LLM resource for simplicity
    repl = REPL(log_level=LogLevel.DEBUG)
    
    # Test case 1: Simple variable assignment
    print("\nTest 1: Simple variable assignment")
    try:
        await repl.execute("private.a = 10")
        print("✅ Test 1 passed")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test case 2: Single word variable reference
    print("\nTest 2: Single word variable reference")
    try:
        # Variable should already be set from Test 1
        await repl.execute("a")
        print("✅ Test 2 passed")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test case 3: Invalid input
    print("\nTest 3: Invalid input")
    try:
        await repl.execute("hello world")
        print("❌ Test 3 should have failed but passed")
    except Exception as e:
        print(f"✅ Test 3 correctly failed: {e}")
    
    # Test case 4: Multi-line code block
    print("\nTest 4: Multi-line code block")
    code_block = """
if private.a > 5:
    private.b = 20
else:
    private.b = 0
"""
    try:
        await repl.execute(code_block)
        print("✅ Test 4 passed")
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
    
    # Print final context values
    print("\nFinal context values:")
    ctx = repl.get_context()
    print(f"private.a = {ctx.get('private.a')}")
    print(f"private.b = {ctx.get('private.b')}")

if __name__ == "__main__":
    asyncio.run(test_repl())