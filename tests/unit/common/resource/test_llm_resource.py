"""Test the LLMResource class."""

import asyncio
import unittest
from unittest.mock import patch

from dana.common.exceptions import LLMAuthenticationError, LLMContextLengthError, LLMError, LLMProviderError, LLMRateLimitError
from dana.common.sys_resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest, BaseResponse


class TestLLMResource(unittest.TestCase):
    """Test the LLMResource class."""

    def test_mock_llm_call(self):
        """Test LLMResource with a mock_llm_call function."""
        llm_resource = LLMResource(name="test_llm").with_mock_llm_call(True)
        llm_resource._is_available = True  # Set the resource as available

        async def run_test():
            prompt = "Test prompt"
            request = BaseRequest(arguments={"prompt": prompt, "messages": [{"role": "user", "content": prompt}]})
            response = await llm_resource.query(request)

            # Essential OpenAI API response structure
            assert isinstance(response, BaseResponse)
            assert response.success
            assert response.content is not None
            assert response.error is None

        asyncio.run(run_test())

    def test_error_classification(self):
        """Test error classification and handling."""
        from dana.common.types import BaseRequest

        # Create LLMResource and make it available
        llm = LLMResource(name="test_llm", model="openai:gpt-4")
        llm._is_available = True  # Make the resource available
        llm._started = True  # Mark as started to skip initialization

        # Test rate limit error
        rate_limit_error = "Rate limit exceeded"
        with patch.object(llm._query_executor, "query_once") as mock_query_once:
            mock_query_once.side_effect = LLMRateLimitError("openai", 429, rate_limit_error)

            request = BaseRequest(arguments={"messages": [{"role": "user", "content": "test"}]})

            # The error should be caught and returned in the BaseResponse
            response = llm.query_sync(request)
            self.assertFalse(response.success)
            self.assertIsNotNone(response.error)
            self.assertIn(rate_limit_error, str(response.error))

        # Test authentication error
        auth_error = "Invalid API key"
        with patch.object(llm._query_executor, "query_once") as mock_query_once:
            mock_query_once.side_effect = LLMAuthenticationError("openai", 401, auth_error)

            request = BaseRequest(arguments={"messages": [{"role": "user", "content": "test"}]})

            response = llm.query_sync(request)
            self.assertFalse(response.success)
            self.assertIsNotNone(response.error)
            self.assertIn(auth_error, str(response.error))

        # Test context length error
        context_length_error = "Context length exceeded"
        with patch.object(llm._query_executor, "query_once") as mock_query_once:
            mock_query_once.side_effect = LLMContextLengthError("openai", None, context_length_error)

            request = BaseRequest(arguments={"messages": [{"role": "user", "content": "test"}]})

            response = llm.query_sync(request)
            self.assertFalse(response.success)
            self.assertIsNotNone(response.error)
            self.assertIn(context_length_error, str(response.error))

        # Test provider error
        provider_error = "Provider error"
        with patch.object(llm._query_executor, "query_once") as mock_query_once:
            mock_query_once.side_effect = LLMProviderError("openai", None, provider_error)

            request = BaseRequest(arguments={"messages": [{"role": "user", "content": "test"}]})

            response = llm.query_sync(request)
            self.assertFalse(response.success)
            self.assertIsNotNone(response.error)
            self.assertIn(provider_error, str(response.error))

        # Test generic error
        generic_error = "Generic error"
        with patch.object(llm._query_executor, "query_once") as mock_query_once:
            mock_query_once.side_effect = LLMError(f"LLM query failed: {generic_error}")

            request = BaseRequest(arguments={"messages": [{"role": "user", "content": "test"}]})

            response = llm.query_sync(request)
            self.assertFalse(response.success)
            self.assertIsNotNone(response.error)
            self.assertIn(generic_error, str(response.error))

    @patch("dana.common.utils.token_management.TokenManagement.enforce_context_window")
    @patch("dana.common.utils.token_management.TokenManagement.estimate_message_tokens")
    def test_token_management(self, mock_estimate, mock_enforce):
        """Test token management and context window enforcement."""
        # Create a long conversation that exceeds token limits
        long_message = "This is a test message. " * 1000  # Approximately 5000 tokens
        _messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": long_message},
            {"role": "assistant", "content": "I understand your question."},
            {"role": "user", "content": "Can you elaborate?"},
        ]

        # Configure the mocks
        mock_enforce.return_value = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Can you elaborate?"},
        ]
        mock_estimate.return_value = 50  # Mock token count per message

        # Set up LLMResource
        llm_resource = LLMResource(name="test_llm", model="openai:gpt-4")
        llm_resource._is_available = True

        # NOTE : TEMPORARY REMOVE UNTIL WE HAVE A COMPATIBLE VERSION OF: enforce_context_window
        # async def test_context_window():
        #     # Mock the actual client call instead of the higher level method
        #     with patch.object(llm_resource._query_executor, "_client") as mock_client:
        #         # Mock the chat completions create method
        #         mock_response = {"choices": [{"message": {"role": "assistant", "content": "Yes, I can!"}}], "usage": {"total_tokens": 100}}
        #         mock_client.chat.completions.create.return_value.model_dump.return_value = mock_response

        #         # Call query_iterative which will trigger token management
        #         request = {"messages": messages, "max_tokens": 1000, "temperature": 0.7}
        #         result = await llm_resource._query_executor.query_iterative(request)

        #         # Verify TokenManagement.enforce_context_window was called
        #         mock_enforce.assert_called_once()

        #         # Verify the parameters passed to enforce_context_window
        #         call_args = mock_enforce.call_args[1]  # Get keyword arguments
        #         self.assertEqual(call_args["max_tokens"], 1000)
        #         self.assertTrue(call_args["preserve_system_messages"])

        #         # Check that the token estimation was called
        #         self.assertTrue(mock_estimate.called)

        #         # Check that the result contains the expected response
        #         self.assertIn("choices", result)

        # asyncio.run(test_context_window())


if __name__ == "__main__":
    unittest.main()
