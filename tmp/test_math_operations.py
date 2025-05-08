"""Test DANA REPL with various math operations in NLP mode."""

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
        # For testing, we'll just return a simple result
        # In real usage, the LLM would analyze the input and generate appropriate DANA code
        return BaseResponse(success=True, content="private.result = 42")


async def main():
    # Create mock LLM resource
    llm = MockLLMResource()

    # Create REPL with NLP mode enabled
    repl = REPL(llm_resource=llm, nlp_mode=True)

    # Test cases for natural language math operations
    test_cases = [
        "calculate 5 plus 5",
        "calculate 10 minus 3",
        "calculate 4 times 7",
        "calculate 20 divided by 4",
        "add 15 and 25",
        "multiply 6 and 7",
        "what is 8 plus 9",
        "compute 5 * 6",
        "10 + 20",
    ]

    for test_input in test_cases:
        print(f"\n----- Testing: '{test_input}' -----")
        try:
            result = await repl.execute(test_input)
            print(f"Success! Result: {result}")

            # Print the context to see if the result was stored
            if "private" in repl.context._state and "result" in repl.context._state["private"]:
                print(f"Value in context: private.result = {repl.context._state['private']['result']}")
        except Exception as e:
            print(f"Failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
