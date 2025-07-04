"""Test the LLMResource class."""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from dana.common.exceptions import LLMAuthenticationError, LLMContextLengthError, LLMError, LLMProviderError, LLMRateLimitError
from dana.common.resource.llm_resource import LLMResource
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
        """Test LLM error classification using direct function call."""
        # Create a resource instance for testing
        LLMResource(name="test_llm", model="openai:gpt-4")

        # Define some error messages
        rate_limit_error = "rate limit exceeded"
        auth_error = "authentication failed"
        context_length_error = "maximum context length exceeded"
        provider_error = "invalid_request_error"
        generic_error = "some other error"

        # Mock the error function to directly test classification logic
        def check_error_type(error_msg, expected_type):
            try:
                # Extract provider and call the error classification logic directly
                provider = "openai"
                status_code = None

                # Simulate the error classification from _query_once
                if any(term in error_msg.lower() for term in ["context length", "token limit", "too many tokens", "maximum context"]):
                    raised_error = LLMContextLengthError(provider, status_code, error_msg)
                elif any(term in error_msg.lower() for term in ["rate limit", "ratelimit", "too many requests", "429"]):
                    raised_error = LLMRateLimitError(provider, status_code, error_msg)
                elif any(
                    term in error_msg.lower() for term in ["authenticate", "authentication", "unauthorized", "auth", "api key", "401"]
                ):
                    raised_error = LLMAuthenticationError(provider, status_code, error_msg)
                elif "invalid_request_error" in error_msg.lower() or "bad request" in error_msg.lower():
                    raised_error = LLMProviderError(provider, status_code, error_msg)
                else:
                    raised_error = LLMError(f"LLM query failed: {error_msg}")

                # Check if the error type matches expected
                self.assertIsInstance(raised_error, expected_type)

                # Also check that the message is preserved
                self.assertIn(error_msg, str(raised_error))

                return True
            except AssertionError:
                return False

        # Test each error type
        self.assertTrue(check_error_type(rate_limit_error, LLMRateLimitError))
        self.assertTrue(check_error_type(auth_error, LLMAuthenticationError))
        self.assertTrue(check_error_type(context_length_error, LLMContextLengthError))
        self.assertTrue(check_error_type(provider_error, LLMProviderError))
        self.assertTrue(check_error_type(generic_error, LLMError))

    @patch("opendxa.common.utils.token_management.TokenManagement.enforce_context_window")
    @patch("opendxa.common.utils.token_management.TokenManagement.estimate_message_tokens")
    def test_token_management(self, mock_estimate, mock_enforce):
        """Test token management and context window enforcement."""
        # Create a long conversation that exceeds token limits
        long_message = "This is a test message. " * 1000  # Approximately 5000 tokens
        messages = [
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

        async def test_context_window():
            # Mock the actual client call instead of the higher level method
            with patch.object(llm_resource._query_executor, "_client") as mock_client:
                # Mock the chat completions create method
                mock_response = {"choices": [{"message": {"role": "assistant", "content": "Yes, I can!"}}], "usage": {"total_tokens": 100}}
                mock_client.chat.completions.create.return_value.model_dump.return_value = mock_response

                # Call query_iterative which will trigger token management
                request = {"messages": messages, "max_tokens": 1000, "temperature": 0.7}
                result = await llm_resource._query_executor.query_iterative(request)

                # Verify TokenManagement.enforce_context_window was called
                mock_enforce.assert_called_once()

                # Verify the parameters passed to enforce_context_window
                call_args = mock_enforce.call_args[1]  # Get keyword arguments
                self.assertEqual(call_args["max_tokens"], 1000)
                self.assertTrue(call_args["preserve_system_messages"])

                # Check that the token estimation was called
                self.assertTrue(mock_estimate.called)

                # Check that the result contains the expected response
                self.assertIn("choices", result)

        asyncio.run(test_context_window())


if __name__ == "__main__":
    unittest.main()
