"""Test script for DANA REPL's NLP mode functionality."""

import asyncio
from opendxa.dana.runtime.repl import REPL
from opendxa.dana.runtime.interpreter import LogLevel
from opendxa.common.resource.llm_resource import LLMResource

async def test_nlp_mode():
    """Test the NLP mode functionality in the REPL."""
    print("\n=== Testing DANA REPL NLP Mode ===\n")
    
    # Mock LLM resource for testing
    # In a real scenario, this would be a real LLM resource
    # But for testing, we'll just create a minimally functional mock
    class MockLLMResource(LLMResource):
        async def initialize(self):
            self.model = "mock-model"
            return True
            
        async def generate(self, prompt, **kwargs):
            # For testing, return a simple DANA code snippet
            # that sets a result variable
            return f"private.result = 42; // Transcoded from: {prompt}"
            
    # Create a mock LLM resource
    llm = MockLLMResource(name="test_llm")
    await llm.initialize()
    
    # Initialize REPL with NLP mode disabled initially
    repl = REPL(llm_resource=llm, log_level=LogLevel.INFO, nlp_mode=False)
    
    # Test 1: NLP mode disabled
    print("\nTest 1: NLP mode disabled - natural language input should fail")
    try:
        await repl.execute("add 5 and 3")
        print("❌ Test 1 failed - should have raised an error")
    except Exception as e:
        print(f"✅ Test 1 passed - error was raised as expected: {e}")
    
    # Test 2: Enable NLP mode
    print("\nTest 2: Enable NLP mode")
    repl.set_nlp_mode(True)
    print(f"NLP mode is now: {repl.is_nlp_mode_enabled()}")
    
    # Test 3: Try natural language with NLP mode enabled
    print("\nTest 3: Natural language with NLP mode enabled")
    try:
        await repl.execute("add 5 and 3")
        # Get the result from the context
        result = repl.context._state["private"].get("result")
        if result == 42:
            print(f"✅ Test 3 passed - transcoding worked, result = {result}")
        else:
            print(f"❌ Test 3 failed - unexpected result: {result}")
    except Exception as e:
        print(f"❌ Test 3 failed - error: {e}")
    
    # Test 4: Direct DANA code still works with NLP mode
    print("\nTest 4: Direct DANA code with NLP mode enabled")
    try:
        await repl.execute("private.direct = 100")
        result = repl.context._state["private"].get("direct")
        if result == 100:
            print(f"✅ Test 4 passed - direct DANA code works, result = {result}")
        else:
            print(f"❌ Test 4 failed - unexpected result: {result}")
    except Exception as e:
        print(f"❌ Test 4 failed - error: {e}")
        
    # Test 5: Disable NLP mode again
    print("\nTest 5: Disable NLP mode")
    repl.set_nlp_mode(False)
    print(f"NLP mode is now: {repl.is_nlp_mode_enabled()}")
    
    # Print final context values
    print("\nFinal context values:")
    for key, value in repl.context._state["private"].items():
        if not key.startswith("__"):  # Skip internal variables
            print(f"  private.{key} = {value}")
            
    print("\n=== Tests complete ===")

if __name__ == "__main__":
    asyncio.run(test_nlp_mode())