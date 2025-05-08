"""Test the token management utility."""

import unittest

from opendxa.common.utils.token_management import TokenManagement


class TestTokenManagement(unittest.TestCase):
    """Test the TokenManagement class."""

    def test_estimate_tokens(self):
        """Test token estimation for strings."""
        # Test empty string
        self.assertEqual(TokenManagement.estimate_tokens(""), 0)

        # Test short string
        short_text = "Hello world"
        short_tokens = TokenManagement.estimate_tokens(short_text)
        self.assertTrue(0 < short_tokens < 5, f"Expected 1-4 tokens, got {short_tokens}")

        # Test longer string
        long_text = "This is a longer text that should have more tokens. " * 10
        long_tokens = TokenManagement.estimate_tokens(long_text)
        self.assertTrue(long_tokens > 40, f"Expected >40 tokens, got {long_tokens}")

    def test_estimate_message_tokens(self):
        """Test token estimation for messages."""
        # Test simple user message
        user_msg = {"role": "user", "content": "Hello, how are you?"}
        user_tokens = TokenManagement.estimate_message_tokens(user_msg)
        self.assertTrue(user_tokens > 5, f"Expected >5 tokens, got {user_tokens}")

        # Test system message
        system_msg = {"role": "system", "content": "You are a helpful assistant."}
        system_tokens = TokenManagement.estimate_message_tokens(system_msg)
        self.assertTrue(system_tokens > 5, f"Expected >5 tokens, got {system_tokens}")

        # Test message with tool calls
        tool_msg = {
            "role": "assistant",
            "content": "I'll help you with that.",
            "tool_calls": [{"function": {"name": "search", "arguments": '{"query": "weather in San Francisco"}'}}],
        }
        tool_tokens = TokenManagement.estimate_message_tokens(tool_msg)
        self.assertTrue(tool_tokens > 10, f"Expected >10 tokens, got {tool_tokens}")

    def test_get_model_token_limit(self):
        """Test getting token limits for different models."""
        # Test known model
        gpt4_limit = TokenManagement.get_model_token_limit("openai:gpt-4")
        self.assertEqual(gpt4_limit, 8192)

        # Test known model with prefixed provider
        claude_limit = TokenManagement.get_model_token_limit("anthropic:claude-3-opus")
        self.assertEqual(claude_limit, 200000)

        # Test unknown model (should return default)
        unknown_limit = TokenManagement.get_model_token_limit("unknown:model")
        self.assertEqual(unknown_limit, 4096)

        # Test provider fallback
        openai_limit = TokenManagement.get_model_token_limit("openai:unknown-model")
        self.assertEqual(openai_limit, 4096)

    def test_enforce_context_window(self):
        """Test context window enforcement."""
        # Create a long conversation
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "How can I help you?"},
            {"role": "user", "content": "Tell me about token limits"},
            {"role": "assistant", "content": "Token limits determine how much text can be processed."},
            {"role": "user", "content": "Can you explain more?"},
        ]

        # Test with a large token limit - should keep all messages
        enforced = TokenManagement.enforce_context_window(
            messages=messages.copy(),
            max_tokens=1000,  # Large enough to keep all messages
            preserve_system_messages=True,
            preserve_latest_messages=2,
        )

        # With enough tokens, all messages should be preserved
        self.assertEqual(len(enforced), len(messages))

        # Test preservation of explicit recent messages
        enforced = TokenManagement.enforce_context_window(
            messages=messages.copy(),
            max_tokens=50,  # Small limit to force truncation
            preserve_system_messages=True,
            preserve_latest_messages=2,  # Explicitly preserve the last 2 messages
        )

        # Should have fewer than the original messages
        self.assertLess(len(enforced), len(messages))

        # Should always preserve system messages
        self.assertTrue(any(msg["role"] == "system" for msg in enforced), "System message should be preserved")

        # Print the messages to understand what's happening
        for msg in enforced:
            if msg["role"] == "system":
                self.assertEqual(msg["content"], "You are a helpful assistant.")

        # Test extreme truncation (tiny limit, don't preserve system messages)
        extreme = TokenManagement.enforce_context_window(
            messages=messages.copy(), max_tokens=20, preserve_system_messages=False, preserve_latest_messages=1
        )

        # Should keep a very small number of messages
        self.assertLessEqual(len(extreme), 2)

        # Check message ordering is maintained
        test_msgs = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
            {"role": "assistant", "content": "Response 2"},
        ]

        ordered = TokenManagement.enforce_context_window(
            messages=test_msgs.copy(),
            max_tokens=1000,  # Large enough to keep all
        )

        # Order should be maintained
        self.assertEqual(len(ordered), len(test_msgs))
        for i, msg in enumerate(ordered):
            self.assertEqual(msg["content"], test_msgs[i]["content"])


if __name__ == "__main__":
    unittest.main()
