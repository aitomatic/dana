"""Test the LLMResource class."""

import unittest
import asyncio
from opendxa import LLMResource, ResourceResponse

class TestLLMResource(unittest.TestCase):
    """Test the LLMResource class."""
    
    def test_mock_llm_call(self):
        """Test LLMResource with a mock_llm_call function."""
        llm_resource = LLMResource(name="test_llm").with_mock_llm_call(True)

        async def run_test():
            prompt = "Test prompt"
            response = await llm_resource.query({"prompt": prompt})
            
            # Essential OpenAI API response structure
            assert isinstance(response, ResourceResponse)
            assert response.success
            assert response.content is not None
            assert response.error is None

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main() 
