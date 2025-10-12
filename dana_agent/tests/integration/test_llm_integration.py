"""
Integration tests for LLM components
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage, LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    """Mock provider for testing"""

    def __init__(self, response_content="Integration test response"):
        self.model = "test-model"
        self.response_content = response_content

    async def chat(self, messages, **kwargs):
        return LLMResponse(
            content=self.response_content,
            model=self.model,
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            finish_reason="stop",
        )

    async def stream(self, messages, **kwargs):
        """Mock streaming response"""
        yield LLMResponse(
            content=self.response_content,
            model=self.model,
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            finish_reason="stop",
        )


class TestLLMIntegration:
    """Integration tests for LLM components working together"""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing"""
        return MockProvider()

    @pytest.mark.asyncio
    async def test_llm_with_factory_provider_creation(self):
        """Test LLM working with factory-created provider"""
        mock_provider = Mock()
        mock_provider.chat = AsyncMock()
        mock_provider.chat.return_value = LLMResponse(content="Integration test response", model="test-model")
        mock_provider.model = "test-model"

        with patch("dana.common.llm.llm.create_provider") as mock_create:
            mock_create.return_value = mock_provider

            llm = LLM(provider="openai", model="gpt-4")
            response = await llm.ask("Hello, world!")

            assert response == "Integration test response"
            mock_create.assert_called_once_with("openai", model="gpt-4")
            mock_provider.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_conversation_flow(self, mock_provider):
        """Test complete conversation flow with LLM"""
        llm = LLM(provider=mock_provider)

        # First message using chat method
        response1 = await llm.chat([LLMMessage(role="user", content="What is 2+2?")])
        assert response1 == "Integration test response"

        # Second message
        response2 = await llm.chat([LLMMessage(role="user", content="What about 3+3?")])
        assert response2 == "Integration test response"

    @pytest.mark.asyncio
    async def test_llm_provider_switching(self, mock_provider):
        """Test switching providers during conversation"""
        llm = LLM(provider=mock_provider)

        # First message with original provider
        response1 = await llm.chat([LLMMessage(role="user", content="Hello")])
        assert response1 == "Integration test response"

        # Switch provider
        new_provider = Mock()
        new_provider.chat = AsyncMock()
        new_provider.chat.return_value = LLMResponse(
            content="New provider response", model="new-model", usage={"prompt_tokens": 5, "completion_tokens": 3}, finish_reason="stop"
        )

        with patch("dana.common.llm.llm.create_provider") as mock_create:
            mock_create.return_value = new_provider
            llm.switch_provider("anthropic", model="claude-3")

        # Second message with new provider
        response2 = await llm.chat([LLMMessage(role="user", content="How are you?")])
        assert response2 == "New provider response"

        # Verify provider was switched
        assert llm.provider == new_provider
        mock_create.assert_called_once_with("anthropic", model="claude-3")

    @pytest.mark.asyncio
    async def test_llm_streaming_integration(self):
        """Test streaming functionality integration"""

        # Create a mock provider that inherits from LLMProvider
        class StreamingMockProvider(LLMProvider):
            def __init__(self):
                self.model = "test-model"

            async def chat(self, messages, **kwargs):
                return LLMResponse(content="Hello from streaming!", model="test-model")

            async def stream(self, messages, **kwargs):
                """Mock streaming response"""
                yield LLMResponse(content="Hello from streaming!", model="test-model")

        mock_provider = StreamingMockProvider()
        llm = LLM(provider=mock_provider)

        responses = []
        async for response in llm.stream([LLMMessage(role="user", content="Test streaming")]):
            responses.append(response)

        # The stream method returns a single response, not multiple chunks
        assert len(responses) == 1
        assert responses[0] == "Hello from streaming!"

    @pytest.mark.asyncio
    async def test_llm_system_prompt_integration(self, mock_provider):
        """Test system prompt integration with conversation"""
        llm = LLM(provider=mock_provider)

        # Test using ask method with system prompt
        response = await llm.ask("What is 5+5?", system_prompt="You are a helpful math tutor.")
        assert response == "Integration test response"

    def test_llm_static_methods_integration(self):
        """Test static methods integration with config manager"""
        with patch("dana.common.llm.llm.config_manager") as mock_config:
            mock_config.get_available_providers.return_value = ["openai", "anthropic", "groq"]
            mock_config.get_provider_config.return_value = {"api_key_env": "OPENAI_API_KEY"}
            mock_config.is_provider_available.return_value = True

            # Test static methods
            providers = LLM.get_available_providers()
            assert providers == ["openai", "anthropic", "groq"]

            is_available = LLM.is_provider_available("openai")
            assert is_available is True

            # The show_config_documentation method prints to stdout and returns None
            documentation = LLM.show_config_documentation()
            assert documentation is None

    @pytest.mark.asyncio
    async def test_llm_error_handling_integration(self):
        """Test error handling integration"""

        # Create a mock provider that inherits from LLMProvider and raises an error
        class ErrorMockProvider(LLMProvider):
            def __init__(self):
                self.model = "test-model"

            async def chat(self, messages, **kwargs):
                raise Exception("Provider error")

        mock_provider = ErrorMockProvider()
        llm = LLM(provider=mock_provider)

        # Test that errors are properly propagated
        with pytest.raises(Exception, match="Provider error"):
            await llm.chat([LLMMessage(role="user", content="Test question")])

    @pytest.mark.asyncio
    async def test_llm_ask_question_static_integration(self):
        """Test static ask_question method integration"""
        mock_provider = Mock()
        mock_provider.chat = AsyncMock()
        mock_provider.chat.return_value = LLMResponse(content="Integration test response", model="test-model")
        mock_provider.model = "test-model"

        with patch("dana.common.llm.llm.create_provider") as mock_create:
            mock_create.return_value = mock_provider

            response = await LLM.ask_question("Static question", provider="openai", model="gpt-4")

            assert response == "Integration test response"
            mock_create.assert_called_once_with("openai", model="gpt-4")
            mock_provider.chat.assert_called_once()
