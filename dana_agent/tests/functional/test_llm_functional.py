"""
Functional tests for LLM components
"""

from unittest.mock import patch

import pytest

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage, LLMProvider, LLMResponse


class MockOpenAIProvider(LLMProvider):
    """Mock OpenAI provider for testing"""

    def __init__(self):
        self.model = "gpt-4"

    async def chat(self, messages, **kwargs):
        return LLMResponse(
            content="OpenAI response", model=self.model, usage={"prompt_tokens": 10, "completion_tokens": 5}, finish_reason="stop"
        )


class MockAnthropicProvider(LLMProvider):
    """Mock Anthropic provider for testing"""

    def __init__(self):
        self.model = "claude-3-sonnet"

    async def chat(self, messages, **kwargs):
        return LLMResponse(
            content="Anthropic response", model=self.model, usage={"prompt_tokens": 10, "completion_tokens": 5}, finish_reason="stop"
        )


class ConfigurableMockProvider(LLMProvider):
    """Mock provider that can be configured for different test scenarios"""

    def __init__(self, response_content="Test response", should_raise=False):
        self.model = "test-model"
        self.response_content = response_content
        self.should_raise = should_raise

    async def chat(self, messages, **kwargs):
        if self.should_raise:
            raise Exception("API error")

        return LLMResponse(
            content=self.response_content, model=self.model, usage={"prompt_tokens": 10, "completion_tokens": 5}, finish_reason="stop"
        )

    async def stream(self, messages, **kwargs):
        """Mock streaming response"""
        if self.should_raise:
            raise Exception("API error")

        yield LLMResponse(
            content=self.response_content, model=self.model, usage={"prompt_tokens": 10, "completion_tokens": 5}, finish_reason="stop"
        )


class TestLLMFunctional:
    """Functional tests for complete LLM workflows"""

    @pytest.fixture
    def mock_openai_provider(self):
        """Create a mock OpenAI provider for testing"""
        return MockOpenAIProvider()

    @pytest.fixture
    def mock_anthropic_provider(self):
        """Create a mock Anthropic provider for testing"""
        return MockAnthropicProvider()

    @pytest.mark.asyncio
    async def test_complete_conversation_workflow(self, mock_openai_provider):
        """Test complete conversation workflow from start to finish"""
        with patch("dana.common.llm.llm.create_provider") as mock_create:
            mock_create.return_value = mock_openai_provider

            # Initialize LLM
            llm = LLM(provider="openai", model="gpt-4")

            # Start conversation with system prompt
            messages1 = [
                LLMMessage(role="system", content="You are a helpful assistant specialized in mathematics."),
                LLMMessage(role="user", content="What is 2+2?"),
            ]
            response1 = await llm.chat(messages1)
            assert response1 == "OpenAI response"

            # Continue conversation
            messages2 = [
                LLMMessage(role="system", content="You are a helpful assistant specialized in mathematics."),
                LLMMessage(role="user", content="What is 2+2?"),
                LLMMessage(role="assistant", content="OpenAI response"),
                LLMMessage(role="user", content="What about 3+3?"),
            ]
            response2 = await llm.chat(messages2)
            assert response2 == "OpenAI response"

    @pytest.mark.asyncio
    async def test_provider_switching_workflow(self, mock_openai_provider, mock_anthropic_provider):
        """Test complete workflow with provider switching"""
        with patch("dana.common.llm.llm.create_provider") as mock_create:
            # Start with OpenAI
            mock_create.return_value = mock_openai_provider
            llm = LLM(provider="openai", model="gpt-4")

            # First conversation with OpenAI
            response1 = await llm.chat([LLMMessage(role="user", content="Hello, I need help with math.")])
            assert response1 == "OpenAI response"
            assert llm.provider == mock_openai_provider

            # Switch to Anthropic
            mock_create.return_value = mock_anthropic_provider
            llm.switch_provider("anthropic", model="claude-3-sonnet")

            # Continue conversation with Anthropic (manually manage conversation history)
            messages = [
                LLMMessage(role="user", content="Hello, I need help with math."),
                LLMMessage(role="assistant", content="OpenAI response"),
                LLMMessage(role="user", content="Can you help me with calculus?"),
            ]
            response2 = await llm.chat(messages)
            assert response2 == "Anthropic response"
            assert llm.provider == mock_anthropic_provider

    @pytest.mark.asyncio
    async def test_streaming_workflow(self):
        """Test complete streaming workflow"""
        streaming_provider = ConfigurableMockProvider(response_content="This is a streaming response.")

        with patch("dana.common.llm.llm.create_provider") as mock_create:
            mock_create.return_value = streaming_provider
            llm = LLM(provider="openai", model="gpt-4")

            # Test streaming
            responses = []
            async for response in llm.stream([LLMMessage(role="user", content="Generate a streaming response")]):
                responses.append(response)

            # The stream method returns a single response, not multiple chunks
            assert len(responses) == 1
            assert responses[0].content == "This is a streaming response."

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test error recovery workflow"""
        error_provider = ConfigurableMockProvider(should_raise=True)
        working_provider = ConfigurableMockProvider(response_content="Anthropic response")

        with patch("dana.common.llm.llm.create_provider") as mock_create:
            # Start with provider that will fail
            mock_create.return_value = error_provider
            llm = LLM(provider="openai", model="gpt-4")

            # First attempt fails
            with pytest.raises(Exception, match="API error"):
                await llm.chat([LLMMessage(role="user", content="Test question")])

            # Switch to working provider
            mock_create.return_value = working_provider
            llm.switch_provider("anthropic", model="claude-3-sonnet")

            # Second attempt succeeds
            response = await llm.chat([LLMMessage(role="user", content="Test question")])
            assert response == "Anthropic response"

    @pytest.mark.asyncio
    async def test_static_methods_workflow(self):
        """Test static methods workflow"""
        with patch("dana.common.llm.llm.config_manager") as mock_config:
            mock_config.get_available_providers.return_value = ["openai", "anthropic", "groq", "ollama"]
            mock_config.is_provider_available.side_effect = lambda provider: provider != "unknown"
            mock_config.get_provider_models.return_value = {"gpt-4": "GPT-4", "gpt-3.5-turbo": "GPT-3.5 Turbo"}

            # Test provider discovery
            providers = LLM.get_available_providers()
            assert "openai" in providers
            assert "anthropic" in providers
            assert "groq" in providers
            assert "ollama" in providers

            # Test provider availability
            is_openai_available = LLM.is_provider_available("openai")
            assert is_openai_available is True

            is_unknown_available = LLM.is_provider_available("unknown")
            assert is_unknown_available is False

            # Test model listing
            models = LLM.get_provider_models("openai")
            assert models == {"gpt-4": "GPT-4", "gpt-3.5-turbo": "GPT-3.5 Turbo"}

            # Test documentation
            docs = LLM.show_config_documentation()
            assert docs is None  # This method prints to stdout and returns None

    @pytest.mark.asyncio
    async def test_mixed_provider_workflow(self, mock_openai_provider, mock_anthropic_provider):
        """Test workflow using different providers for different tasks"""
        with patch("dana.common.llm.llm.create_provider") as mock_create:
            # Use OpenAI for general questions
            mock_create.return_value = mock_openai_provider
            llm1 = LLM(provider="openai", model="gpt-4")

            # Use Anthropic for creative tasks
            mock_create.return_value = mock_anthropic_provider
            llm2 = LLM(provider="anthropic", model="claude-3-sonnet")

            # Test both providers independently
            response1 = await llm1.chat([LLMMessage(role="user", content="What is the capital of France?")])
            assert response1 == "OpenAI response"

            response2 = await llm2.chat([LLMMessage(role="user", content="Write a creative story about a robot.")])
            assert response2 == "Anthropic response"

    @pytest.mark.asyncio
    async def test_complex_conversation_workflow(self, mock_openai_provider):
        """Test complex conversation with multiple interactions"""
        with patch("dana.common.llm.llm.create_provider") as mock_create:
            mock_create.return_value = mock_openai_provider
            llm = LLM(provider="openai", model="gpt-4")

            # Simulate a coding session with stateless LLM
            # First interaction
            messages1 = [
                LLMMessage(role="system", content="You are a helpful coding assistant."),
                LLMMessage(role="user", content="I need help with Python."),
            ]
            response1 = await llm.chat(messages1)
            assert response1 == "OpenAI response"

            # Second interaction
            messages2 = [
                LLMMessage(role="system", content="You are a helpful coding assistant."),
                LLMMessage(role="user", content="I need help with Python."),
                LLMMessage(role="assistant", content="OpenAI response"),
                LLMMessage(role="user", content="How do I create a list?"),
            ]
            response2 = await llm.chat(messages2)
            assert response2 == "OpenAI response"
