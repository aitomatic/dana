"""
Unit tests for the core LLM module
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage, LLMProvider, LLMResponse, ProviderError


class MockProvider(LLMProvider):
    """Mock provider for testing"""

    def __init__(self, response_content="Test response"):
        self.model = "test-model"
        self.response_content = response_content

    async def chat(self, messages, **kwargs):
        return LLMResponse(
            content=self.response_content, model=self.model, usage={"prompt_tokens": 10, "completion_tokens": 5}, finish_reason="stop"
        )

    async def stream(self, messages, **kwargs):
        """Mock streaming response"""
        yield LLMResponse(
            content=self.response_content, model=self.model, usage={"prompt_tokens": 10, "completion_tokens": 5}, finish_reason="stop"
        )


class TestLLMCore:
    """Unit tests for the core LLM class"""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing"""
        return MockProvider()

    @pytest.fixture
    def llm(self, mock_provider):
        """Create an LLM instance with mock provider"""
        return LLM(provider=mock_provider)

    def test_init_with_provider_string(self):
        """Test LLM initialization with provider string"""
        with patch("dana_agent.common.llm.llm.create_provider") as mock_create:
            mock_provider = Mock()
            mock_create.return_value = mock_provider

            llm = LLM(provider="openai", model="gpt-4")

            mock_create.assert_called_once_with("openai", model="gpt-4")
            assert llm.provider == mock_provider

    def test_init_with_provider_object(self, mock_provider):
        """Test LLM initialization with provider object"""
        llm = LLM(provider=mock_provider)
        assert llm.provider == mock_provider

    def test_init_with_default_provider(self):
        """Test LLM initialization with default provider"""
        with patch("dana_agent.common.llm.llm.create_provider") as mock_create:
            mock_provider = Mock()
            mock_create.return_value = mock_provider

            llm = LLM()

            mock_create.assert_called_once()
            assert llm.provider == mock_provider

    @pytest.mark.asyncio
    async def test_chat(self, llm):
        """Test chat method"""
        response = await llm.chat([LLMMessage(role="user", content="Hello")])

        assert response == "Test response"

    @pytest.mark.asyncio
    async def test_ask(self, llm):
        """Test ask method"""
        response = await llm.ask("What is 2+2?")

        assert response == "Test response"

        # The ask method doesn't add messages to conversation history
        # It creates a temporary messages list for the call

    @pytest.mark.asyncio
    async def test_ask_with_system_prompt(self, llm):
        """Test ask method with system prompt"""
        response = await llm.ask("What is 2+2?", system_prompt="You are a math tutor")

        assert response == "Test response"

    @pytest.mark.asyncio
    async def test_stream(self, llm):
        """Test stream method"""
        responses = []
        async for response in llm.stream([LLMMessage(role="user", content="Hello")]):
            responses.append(response)

        # The stream method returns a single response, not multiple chunks
        assert len(responses) == 1
        assert responses[0] == "Test response"

    def test_switch_provider(self, llm):
        """Test switch_provider method"""
        with patch("dana_agent.common.llm.llm.create_provider") as mock_create:
            new_provider = Mock()
            mock_create.return_value = new_provider

            llm.switch_provider("anthropic", model="claude-3")

            mock_create.assert_called_once_with("anthropic", model="claude-3")
            assert llm.provider == new_provider

    @pytest.mark.asyncio
    async def test_ask_question_static(self, mock_provider):
        """Test static ask_question method"""
        with patch("dana_agent.common.llm.llm.create_provider") as mock_create:
            mock_create.return_value = mock_provider

            response = await LLM.ask_question("Hello", provider="openai")

            assert response == "Test response"
            mock_create.assert_called_once_with("openai", model=None)

    def test_get_available_providers(self):
        """Test get_available_providers static method"""
        with patch("dana_agent.common.llm.llm.config_manager") as mock_config:
            mock_config.get_available_providers.return_value = ["openai", "anthropic"]

            providers = LLM.get_available_providers()

            assert providers == ["openai", "anthropic"]
            mock_config.get_available_providers.assert_called_once()

    def test_is_provider_available(self):
        """Test is_provider_available static method"""
        with patch("dana_agent.common.llm.llm.config_manager") as mock_config:
            mock_config.is_provider_available.return_value = True

            is_available = LLM.is_provider_available("openai")

            assert is_available is True
            mock_config.is_provider_available.assert_called_once_with("openai")

    def test_get_provider_models(self):
        """Test get_provider_models static method"""
        with patch("dana_agent.common.llm.llm.config_manager") as mock_config:
            mock_config.get_provider_models.return_value = {"gpt-4": "GPT-4", "gpt-3.5-turbo": "GPT-3.5 Turbo"}

            models = LLM.get_provider_models("openai")

            assert models == {"gpt-4": "GPT-4", "gpt-3.5-turbo": "GPT-3.5 Turbo"}
            mock_config.get_provider_models.assert_called_once_with("openai")

    def test_show_config_documentation(self):
        """Test show_config_documentation static method"""
        # The show_config_documentation method prints to stdout and returns None
        result = LLM.show_config_documentation()

        assert result is None

    @pytest.mark.asyncio
    async def test_chat_empty_messages(self, llm):
        """Test chat with empty messages list raises ValueError"""
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            await llm.chat([])

    @pytest.mark.asyncio
    async def test_ask_empty_question(self, llm):
        """Test ask with empty question raises ValueError"""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            await llm.ask("")

        with pytest.raises(ValueError, match="Question cannot be empty"):
            await llm.ask("   ")

    @pytest.mark.asyncio
    async def test_stream_empty_messages(self, llm):
        """Test stream with empty messages list raises ValueError"""
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            async for _ in llm.stream([]):
                pass

    @pytest.mark.asyncio
    async def test_chat_provider_error(self, llm):
        """Test chat propagates provider errors as ProviderError"""
        # Mock provider to raise an exception
        llm.provider.chat = AsyncMock(side_effect=Exception("Provider error"))

        with pytest.raises(ProviderError, match="Chat failed with custom: Provider error"):
            await llm.chat([LLMMessage(role="user", content="test")])

    @pytest.mark.asyncio
    async def test_stream_provider_error(self, llm):
        """Test stream propagates provider errors as ProviderError"""

        # Mock provider to raise an exception
        async def mock_stream(*args, **kwargs):
            raise Exception("Provider error")
            yield  # This line will never be reached, but makes it an async generator

        llm.provider.stream = mock_stream

        with pytest.raises(ProviderError, match="Stream failed with custom: Provider error"):
            async for _ in llm.stream([LLMMessage(role="user", content="test")]):
                pass
