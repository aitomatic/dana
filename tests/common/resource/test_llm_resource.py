"""Test the LLMResource class."""

import unittest
import asyncio
from opendxa.common.resource.llm_resource import LLMResource

class TestLLMResource(unittest.TestCase):
    """Test the LLMResource class."""
    
    def test_mock_llm_call(self):
        """Test LLMResource with a mock_llm_call function."""
        llm_resource = LLMResource(name="test_llm").with_mock_llm_call(True)

        async def run_test():
            prompt = "Test prompt"
            response = await llm_resource.query({"prompt": prompt})  # Ensure this is awaited
            self.assertEqual(response["content"], f"Echo: {prompt}")

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main() 