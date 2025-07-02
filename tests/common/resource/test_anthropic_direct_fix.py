"""Direct unit test for Anthropic system message format fix.

This test directly tests the _build_default_request_params method
to verify that the fix correctly transforms system messages for Anthropic.
"""

from opendxa.common.resource.llm_query_executor import LLMQueryExecutor


class TestAnthropicDirectFix:
    """Direct unit test for the Anthropic system message fix."""

    def test_anthropic_system_message_transformation(self):
        """Test that Anthropic models keep system messages in messages array for AISuite."""
        # Create LLMQueryExecutor with Anthropic model
        executor = LLMQueryExecutor(model="anthropic:claude-3-5-sonnet-20240620")

        # Create request with system message in messages array
        request = {
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant. Respond concisely and accurately."},
                {"role": "user", "content": "what is pi?"},
            ],
            "temperature": 0.7,
        }

        # Call the method we fixed
        result = executor._build_default_request_params(request)

        # Verify NO manual system parameter is added (AISuite handles this)
        assert "system" not in result, "No manual system parameter should be added to avoid conflicts"

        # Verify system messages remain in messages array for AISuite to handle
        messages = result["messages"]
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        assert len(system_messages) == 1, "System messages should remain in messages array for AISuite"
        assert system_messages[0]["content"] == "You are a helpful AI assistant. Respond concisely and accurately."

        # Verify user message is preserved
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        assert len(user_messages) == 1, "Expected exactly one user message"
        assert user_messages[0]["content"] == "what is pi?"

        # Verify other parameters are preserved
        assert result["model"] == "anthropic:claude-3-5-sonnet-20240620"
        assert result["temperature"] == 0.7

    def test_anthropic_multiple_system_messages_preserved(self):
        """Test that multiple system messages are preserved for AISuite to handle."""
        executor = LLMQueryExecutor(model="anthropic:claude-3-haiku-20240307")

        request = {
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "system", "content": "Respond concisely and accurately."},
                {"role": "user", "content": "what is pi?"},
            ]
        }

        result = executor._build_default_request_params(request)

        # No manual system parameter should be created
        assert "system" not in result, "No manual system parameter should be created"

        # All system messages should remain in messages array for AISuite
        messages = result["messages"]
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        assert len(system_messages) == 2, "All system messages should remain for AISuite"
        assert system_messages[0]["content"] == "You are a helpful AI assistant."
        assert system_messages[1]["content"] == "Respond concisely and accurately."

    def test_openai_system_message_unchanged(self):
        """Test that OpenAI models keep system messages in messages array."""
        executor = LLMQueryExecutor(model="openai:gpt-4")

        request = {
            "messages": [{"role": "system", "content": "You are a helpful AI assistant."}, {"role": "user", "content": "what is pi?"}],
            "temperature": 0.7,
        }

        result = executor._build_default_request_params(request)

        # OpenAI should NOT have top-level system parameter
        assert "system" not in result, "OpenAI should not have top-level system parameter"

        # System message should remain in messages array for OpenAI
        messages = result["messages"]
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        assert len(system_messages) == 1, "Expected system message in messages array for OpenAI"
        assert system_messages[0]["content"] == "You are a helpful AI assistant."

    def test_groq_system_message_unchanged(self):
        """Test that non-Anthropic models (like Groq) keep system messages in messages array."""
        executor = LLMQueryExecutor(model="groq:llama3-70b-8192")

        request = {
            "messages": [{"role": "system", "content": "You are a helpful AI assistant."}, {"role": "user", "content": "what is pi?"}]
        }

        result = executor._build_default_request_params(request)

        # Groq should NOT have top-level system parameter
        assert "system" not in result, "Groq should not have top-level system parameter"

        # System message should remain in messages array for Groq
        messages = result["messages"]
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        assert len(system_messages) == 1, "Expected system message in messages array for Groq"

    def test_anthropic_no_system_messages_no_system_param(self):
        """Test that Anthropic without system messages doesn't get system parameter."""
        executor = LLMQueryExecutor(model="anthropic:claude-3-opus-20240229")

        request = {"messages": [{"role": "user", "content": "what is pi?"}]}

        result = executor._build_default_request_params(request)

        # Should not have system parameter if no system messages
        assert "system" not in result, "Should not have system parameter when no system messages"

        # Should only have user message
        messages = result["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_anthropic_empty_system_message_preserved(self):
        """Test that empty system messages are preserved for AISuite to handle."""
        executor = LLMQueryExecutor(model="anthropic:claude-3-sonnet-20240229")

        request = {
            "messages": [
                {"role": "system", "content": ""},
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "what is pi?"},
            ]
        }

        result = executor._build_default_request_params(request)

        # No manual system parameter should be created
        assert "system" not in result, "No manual system parameter should be created"

        # All system messages (including empty ones) should be preserved
        messages = result["messages"]
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        assert len(system_messages) == 2, "All system messages should be preserved"
        assert system_messages[0]["content"] == ""
        assert system_messages[1]["content"] == "You are a helpful AI assistant."
