"""Debug script to investigate NLP mode and transcoding issues."""

import asyncio
import traceback

from opendxa.common.types import BaseResponse
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.repl import REPL
from opendxa.dana.transcoder.transcoder import FaultTolerantTranscoder


# Create a mock LLM resource that returns valid DANA code
class MockLLMResource:
    def __init__(self):
        self.provider = "mock"
        self.model = "test"
        self.name = "mock_llm"

    async def query(self, request):
        # Generate specific responses for test inputs
        if "calculate 5 plus 5" in str(request):
            return BaseResponse(success=True, content="private.result = 5 + 5")
        else:
            return BaseResponse(success=True, content="private.result = 42")


async def test_transcoder_directly():
    """Test the transcoder directly without going through the REPL."""
    print("\n==== Testing Transcoder Directly ====")

    # Create mock LLM resource
    llm = MockLLMResource()

    # Create transcoder
    transcoder = FaultTolerantTranscoder(llm)

    # Create context
    context = RuntimeContext()

    # Test input
    test_input = "calculate 5 plus 5"

    try:
        # Direct transcoder call
        print(f"Calling transcoder.transcode() with: '{test_input}'")
        result, code = await transcoder.transcode(test_input, context)

        print(f"Transcoder result valid: {result.is_valid}")
        print(f"Transcoder generated code: {code}")

        if result.is_valid:
            print("✅ Transcoder direct test PASSED")
        else:
            print("❌ Transcoder direct test FAILED")
    except Exception as e:
        print(f"❌ Transcoder direct test ERROR: {e}")
        print(traceback.format_exc())


async def test_repl_execution():
    """Test the REPL's execute method with NLP mode enabled."""
    print("\n==== Testing REPL Execution ====")

    # Create mock LLM resource
    llm = MockLLMResource()

    # Create REPL with NLP mode enabled
    repl = REPL(llm_resource=llm, nlp_mode=True)

    # Test input
    test_input = "calculate 5 plus 5"

    try:
        # REPL execution
        print(f"Calling repl.execute() with: '{test_input}'")
        result = await repl.execute(test_input)

        print(f"REPL execution result: {result}")
        print("✅ REPL execution test PASSED")
    except Exception as e:
        print(f"❌ REPL execution test FAILED: {e}")
        print(traceback.format_exc())


async def main():
    """Run all tests."""
    await test_transcoder_directly()
    await test_repl_execution()


if __name__ == "__main__":
    asyncio.run(main())
