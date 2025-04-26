"""Test the LLMResource class."""

import unittest
import asyncio
from opendxa import LLMResource
from opendxa.common.types import BaseResponse, BaseRequest

class TestLLMResource(unittest.TestCase):
    """Test the LLMResource class."""
    
    def test_mock_llm_call(self):
        """Test LLMResource with a mock_llm_call function."""
        llm_resource = LLMResource(name="test_llm").with_mock_llm_call(True)
        llm_resource._is_available = True  # Set the resource as available

        async def run_test():
            prompt = "Test prompt"
            request = BaseRequest(arguments={
                "prompt": prompt,
                "messages": [{"role": "user", "content": prompt}]
            })
            response = await llm_resource.query(request)
            
            # Essential OpenAI API response structure
            assert isinstance(response, BaseResponse)
            assert response.success
            assert response.content is not None
            assert response.error is None

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main() 
