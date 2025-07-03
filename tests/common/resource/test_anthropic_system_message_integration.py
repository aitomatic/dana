"""Integration tests for Anthropic system message handling.

This test suite verifies that AISuite automatically handles Anthropic system message
transformation, eliminating the need for manual transformation and preventing conflicts.
"""

import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseRequest


class TestAnthropicSystemMessageIntegration(unittest.TestCase):
    """Integration tests for Anthropic system message handling."""

    def setUp(self):
        """Set up test environment."""
        # Enable mock mode to avoid real API calls
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

    def test_aisuite_handles_anthropic_automatically(self):
        """Test that AISuite automatically handles Anthropic system message transformation."""
        llm = LLMResource(model="anthropic:claude-3-5-sonnet-20240620")

        request = BaseRequest(
            arguments={
                "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "What is pi?"}],
                "temperature": 0.7,
            }
        )

        with patch("aisuite.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Track what parameters are sent to AISuite
            captured_params = {}

            def capture_params(*args, **kwargs):
                # Update captured_params with the actual parameters
                for key, value in kwargs.items():
                    captured_params[key] = value

                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message = MagicMock()
                mock_response.choices[0].message.role = "assistant"
                mock_response.choices[0].message.content = "Test response"
                mock_response.choices[0].message.tool_calls = None
                mock_response.usage = MagicMock()
                mock_response.usage.prompt_tokens = 20
                mock_response.usage.completion_tokens = 10
                mock_response.model = "claude-3-5-sonnet-20240620"
                mock_response.model_dump.return_value = {"choices": [{"message": {"role": "assistant", "content": "Test response"}}]}
                return mock_response

            mock_client.chat.completions.create.side_effect = capture_params

            # Execute the query
            result = llm.query_sync(request)

            # Verify that system messages are left in the messages array for AISuite to handle
            messages = captured_params.get("messages", [])
            system_messages = [msg for msg in messages if msg.get("role") == "system"]

            # Should have at least our system message (plus potentially default ones from LLMQueryExecutor)
            self.assertGreaterEqual(len(system_messages), 1, "System messages should remain in messages array for AISuite")

            # Our system message should be present
            user_system_msg = next((msg for msg in system_messages if "helpful assistant" in msg.get("content", "")), None)
            self.assertIsNotNone(user_system_msg, "User's system message should be present")

            # No manual system parameter should be added to avoid conflicts
            self.assertNotIn("system", captured_params, "No manual system parameter should be added to avoid conflicts")
            self.assertTrue(result.success)

    def test_no_manual_transformation_for_anthropic(self):
        """Test that we don't manually transform Anthropic system messages."""
        llm = LLMResource(model="anthropic:claude-3-5-sonnet-20240620")

        request = {"messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "What is pi?"}]}

        # Build request parameters (this should NOT transform for Anthropic)
        result_params = llm._build_request_params(request)

        # Verify that system messages remain in the messages array
        messages = result_params.get("messages", [])
        system_messages = [msg for msg in messages if msg.get("role") == "system"]

        self.assertGreaterEqual(len(system_messages), 1, "System messages should remain for AISuite to handle")
        self.assertNotIn("system", result_params, "No manual system parameter should be added")

    def test_openai_system_messages_unchanged(self):
        """Test that OpenAI system messages remain unchanged (no transformation needed)."""
        llm = LLMResource(model="openai:gpt-4")

        request = BaseRequest(
            arguments={
                "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "What is pi?"}],
                "temperature": 0.7,
            }
        )

        with patch("aisuite.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            captured_params = {}

            def capture_params(*args, **kwargs):
                # Update captured_params with the actual parameters
                for key, value in kwargs.items():
                    captured_params[key] = value

                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message = MagicMock()
                mock_response.choices[0].message.role = "assistant"
                mock_response.choices[0].message.content = "Test response"
                mock_response.choices[0].message.tool_calls = None
                mock_response.usage = MagicMock()
                mock_response.usage.prompt_tokens = 20
                mock_response.usage.completion_tokens = 10
                mock_response.model = "gpt-4"
                mock_response.model_dump.return_value = {"choices": [{"message": {"role": "assistant", "content": "Test response"}}]}
                return mock_response

            mock_client.chat.completions.create.side_effect = capture_params

            result = llm.query_sync(request)

            # Verify OpenAI messages remain unchanged
            messages = captured_params.get("messages", [])
            system_messages = [msg for msg in messages if msg.get("role") == "system"]

            # Should have at least our system message (plus potentially default ones from LLMQueryExecutor)
            self.assertGreaterEqual(len(system_messages), 1, "OpenAI should keep system messages in array")

            # Our system message should be present
            user_system_msg = next((msg for msg in system_messages if "helpful assistant" in msg.get("content", "")), None)
            self.assertIsNotNone(user_system_msg, "User's system message should be present")

            self.assertNotIn("system", captured_params, "OpenAI should not have top-level system parameter")

    def test_multiple_system_messages_handling(self):
        """Test handling of multiple system messages."""
        llm = LLMResource(model="anthropic:claude-3-5-sonnet-20240620")

        request = {
            "messages": [
                {"role": "system", "content": "You are an assistant."},
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hello"},
            ]
        }

        result_params = llm._build_request_params(request)

        # All system messages should remain in the array for AISuite to handle
        messages = result_params.get("messages", [])
        system_messages = [msg for msg in messages if msg.get("role") == "system"]

        self.assertEqual(len(system_messages), 2, "All system messages should remain in array")
        self.assertNotIn("system", result_params, "No manual system parameter should be created")

    def test_no_system_messages_no_issues(self):
        """Test that requests without system messages work normally."""
        llm = LLMResource(model="anthropic:claude-3-5-sonnet-20240620")

        request = {"messages": [{"role": "user", "content": "What is pi?"}]}

        result_params = llm._build_request_params(request)

        messages = result_params.get("messages", [])
        system_messages = [msg for msg in messages if msg.get("role") == "system"]

        self.assertEqual(len(system_messages), 0, "No system messages should be present")
        self.assertNotIn("system", result_params, "No system parameter should be created")


if __name__ == "__main__":
    unittest.main()
