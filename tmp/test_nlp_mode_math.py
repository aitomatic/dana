"""Test DANA REPL NLP mode with math operations."""

import asyncio

from opendxa.common.types import BaseResponse
from opendxa.dana.runtime.repl import REPL


# Create a mock LLM resource that returns valid DANA code
class MockLLMResource:
    def __init__(self):
        self.provider = "mock"
        self.model = "test"
        self.name = "mock_llm"

    async def query(self, request):
        # Return a mock response based on the content of the request
        # This simulates the LLM generating DANA code
        return BaseResponse(success=True, content="private.result = 5 + 5")


async def main():
    # Create mock LLM resource
    llm = MockLLMResource()

    # Create REPL with NLP mode enabled
    repl = REPL(llm_resource=llm, nlp_mode=True)

    # Verify NLP mode is enabled
    nlp_enabled = repl.get_nlp_mode()
    print(f"NLP Mode Enabled: {nlp_enabled}")

    # Test cases for math operations
    test_inputs = ["calculate 5 plus 5", "calculate 10 minus 3", "calculate 4 times 7", "calculate 20 divided by 4", "add 15 and 25"]

    # Run each test case
    for input_text in test_inputs:
        print(f"\n----- Testing: '{input_text}' -----")
        try:
            result = await repl.execute(input_text)
            print(f"Execution successful! Result: {result}")
        except Exception as e:
            print(f"Execution failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
