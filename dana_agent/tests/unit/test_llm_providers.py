"""
Unit tests for LLM providers
"""

from unittest.mock import Mock, patch

import pytest

from dana.common.llm.types import LLMMessage, LLMResponse


class TestOpenAIProvider:
    """Unit tests for OpenAI provider"""

    @pytest.fixture
    def provider(self):
        """Create OpenAIProvider instance for testing"""
        with patch("dana.common.llm.providers.openai.AsyncOpenAI"):
            from dana.common.llm.providers.openai import OpenAIProvider

            return OpenAIProvider(api_key="test-key", model="gpt-4")

    def test_init(self, provider):
        """Test OpenAIProvider initialization"""
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello from OpenAI!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        # Explicitly set prompt_tokens_details to None to avoid Mock returning Mock for cache fields
        mock_response.usage.prompt_tokens_details = None

        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.chat(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Hello from OpenAI!"
            assert response.model == "gpt-4"
            assert response.finish_reason == "stop"
            assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test chat with API error"""
        with patch.object(provider.client.chat.completions, "create") as mock_create:
            mock_create.side_effect = Exception("API Error")

            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(Exception, match="API Error"):
                await provider.chat(messages)


class TestAnthropicProvider:
    """Unit tests for Anthropic provider"""

    @pytest.fixture
    def provider(self):
        """Create AnthropicProvider instance for testing"""
        with patch("dana.common.llm.providers.anthropic.anthropic"):
            from dana.common.llm.providers.anthropic import AnthropicProvider

            return AnthropicProvider(api_key="test-key", model="claude-3-sonnet")

    def test_init(self, provider):
        """Test AnthropicProvider initialization"""
        assert provider.api_key == "test-key"
        assert provider.model == "claude-3-sonnet"

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].type = "text"
        mock_response.content[0].text = "Hello from Anthropic!"
        mock_response.stop_reason = "end_turn"
        mock_response.model = "claude-3-sonnet"
        mock_response.usage = Mock(spec=["input_tokens", "output_tokens"])
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.messages, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.chat(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Hello from Anthropic!"
            assert response.model == "claude-3-sonnet"
            assert response.finish_reason == "end_turn"
            assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test chat with API error"""
        with patch.object(provider.client.messages, "create") as mock_create:
            mock_create.side_effect = Exception("API Error")

            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(Exception, match="API Error"):
                await provider.chat(messages)


class TestAzureProvider:
    """Unit tests for Azure provider"""

    @pytest.fixture
    def provider(self):
        """Create AzureProvider instance for testing"""
        with patch("dana.common.llm.providers.azure.AsyncOpenAI"):
            from dana.common.llm.providers.azure import AzureProvider

            return AzureProvider(
                api_key="test-key", base_url="https://test.openai.azure.com/", api_version="2024-02-15-preview", model="gpt-35-turbo"
            )

    def test_init(self, provider):
        """Test AzureProvider initialization"""
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://test.openai.azure.com/?api-version=2024-02-15-preview"
        assert provider.api_version == "2024-02-15-preview"
        assert provider.model == "gpt-35-turbo"

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello from Azure!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-35-turbo"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.chat(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Hello from Azure!"
            assert response.model == "gpt-35-turbo"
            assert response.finish_reason == "stop"
            assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test chat with API error"""
        with patch.object(provider.client.chat.completions, "create") as mock_create:
            mock_create.side_effect = Exception("API Error")

            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(Exception, match="API Error"):
                await provider.chat(messages)


class TestGroqProvider:
    """Unit tests for Groq provider"""

    @pytest.fixture
    def provider(self):
        """Create GroqProvider instance for testing"""
        with patch("dana.common.llm.providers.groq.AsyncOpenAI"):
            from dana.common.llm.providers.groq import GroqProvider

            return GroqProvider(api_key="test-key", model="llama3-8b-8192")

    def test_init(self, provider):
        """Test GroqProvider initialization"""
        assert provider.api_key == "test-key"
        assert provider.model == "llama3-8b-8192"

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello from Groq!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "llama3-8b-8192"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.chat(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Hello from Groq!"
            assert response.model == "llama3-8b-8192"
            assert response.finish_reason == "stop"
            assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test chat with API error"""
        with patch.object(provider.client.chat.completions, "create") as mock_create:
            mock_create.side_effect = Exception("API Error")

            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(Exception, match="API Error"):
                await provider.chat(messages)


class TestOllamaProvider:
    """Unit tests for Ollama provider"""

    @pytest.fixture
    def provider(self):
        """Create OllamaProvider instance for testing"""
        with patch("dana.common.llm.providers.ollama.AsyncOpenAI"):
            from dana.common.llm.providers.ollama import OllamaProvider

            return OllamaProvider(base_url="http://localhost:11434", model="llama2")

    def test_init(self, provider):
        """Test OllamaProvider initialization"""
        assert provider.base_url == "http://localhost:11434"
        assert provider.model == "llama2"

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello from Ollama!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "llama2"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.chat(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Hello from Ollama!"
            assert response.model == "llama2"
            assert response.finish_reason == "stop"
            assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test chat with API error"""

        # Create an async mock that raises an exception
        async def mock_create(*args, **kwargs):
            raise Exception("API Error")

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(Exception, match="API Error"):
                await provider.chat(messages)


class TestHuggingFaceProvider:
    """Unit tests for HuggingFace provider"""

    @pytest.fixture
    def provider(self):
        """Create HuggingFaceProvider instance for testing"""
        with patch("dana.common.llm.providers.huggingface.AsyncOpenAI"):
            from dana.common.llm.providers.huggingface import HuggingFaceProvider

            return HuggingFaceProvider(api_key="test-key", model="microsoft/DialoGPT-medium")

    def test_init(self, provider):
        """Test HuggingFaceProvider initialization"""
        assert provider.api_key == "test-key"
        assert provider.model == "microsoft/DialoGPT-medium"

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello from HuggingFace!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "microsoft/DialoGPT-medium"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.chat(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Hello from HuggingFace!"
            assert response.model == "microsoft/DialoGPT-medium"
            assert response.finish_reason == "stop"
            assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test chat with API error"""

        # Create an async mock that raises an exception
        async def mock_create(*args, **kwargs):
            raise Exception("API Error")

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(Exception, match="API Error"):
                await provider.chat(messages)


class TestMoonshotProvider:
    """Unit tests for Moonshot provider"""

    @pytest.fixture
    def provider(self):
        """Create MoonshotProvider instance for testing"""
        with patch("dana.common.llm.providers.moonshot.AsyncOpenAI"):
            from dana.common.llm.providers.moonshot import MoonshotProvider

            return MoonshotProvider(api_key="test-key", model="moonshot-v1-8k")

    def test_init(self, provider):
        """Test MoonshotProvider initialization"""
        assert provider.api_key == "test-key"
        assert provider.model == "moonshot-v1-8k"

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello from Moonshot!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "moonshot-v1-8k"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.chat(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Hello from Moonshot!"
            assert response.model == "moonshot-v1-8k"
            assert response.finish_reason == "stop"
            assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test chat with API error"""
        with patch.object(provider.client.chat.completions, "create") as mock_create:
            mock_create.side_effect = Exception("API Error")

            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(Exception, match="API Error"):
                await provider.chat(messages)


class TestQwenProvider:
    """Unit tests for Qwen provider"""

    @pytest.fixture
    def provider(self):
        """Create QwenProvider instance for testing"""
        with patch("dana.common.llm.providers.qwen.AsyncOpenAI"):
            from dana.common.llm.providers.qwen import QwenProvider

            return QwenProvider(api_key="test-key", model="qwen-turbo")

    def test_init(self, provider):
        """Test QwenProvider initialization"""
        assert provider.api_key == "test-key"
        assert provider.model == "qwen-turbo"

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello from Qwen!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "qwen-turbo"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.chat(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Hello from Qwen!"
            assert response.model == "qwen-turbo"
            assert response.finish_reason == "stop"
            assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test chat with API error"""
        with patch.object(provider.client.chat.completions, "create") as mock_create:
            mock_create.side_effect = Exception("API Error")

            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(Exception, match="API Error"):
                await provider.chat(messages)


class TestDeepSeekProvider:
    """Unit tests for DeepSeek provider"""

    @pytest.fixture
    def provider(self):
        """Create DeepSeekProvider instance for testing"""
        with patch("openai.AsyncOpenAI"):
            from dana.common.llm.providers.deepseek import DeepSeekProvider

            return DeepSeekProvider(api_key="test-key", model="deepseek-chat")

    def test_init(self, provider):
        """Test DeepSeekProvider initialization"""
        assert provider.api_key == "test-key"
        assert provider.model == "deepseek-chat"

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello from DeepSeek!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "deepseek-chat"
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 5
        mock_usage.total_tokens = 15
        mock_usage.model_dump.return_value = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        mock_response.usage = mock_usage

        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_response

        # Mock the OpenAI client creation and its chat.completions.create method
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create = mock_create
            mock_openai_class.return_value = mock_client

            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.chat(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Hello from DeepSeek!"
            assert response.model == "deepseek-chat"
            assert response.finish_reason is None  # DeepSeek doesn't set finish_reason
            assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test chat with API error"""

        # Create an async mock that raises an exception
        async def mock_create(*args, **kwargs):
            raise Exception("API Error")

        # Mock the OpenAI client creation and its chat.completions.create method
        with patch("openai.AsyncOpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_client.chat.completions.create = mock_create
            mock_openai_class.return_value = mock_client

            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(Exception, match="API Error"):
                await provider.chat(messages)


class TestOpenRouterProvider:
    """Unit tests for OpenRouter provider"""

    @pytest.fixture
    def provider(self):
        """Create OpenRouterProvider instance for testing"""
        with patch("dana.common.llm.providers.openrouter.AsyncOpenAI"):
            from dana.common.llm.providers.openrouter import OpenRouterProvider

            return OpenRouterProvider(api_key="test-key", model="openai/gpt-3.5-turbo")

    def test_init(self, provider):
        """Test OpenRouterProvider initialization"""
        assert provider.api_key == "test-key"
        assert provider.model == "openai/gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello from OpenRouter!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "openai/gpt-3.5-turbo"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.chat(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "Hello from OpenRouter!"
            assert response.model == "openai/gpt-3.5-turbo"
            assert response.finish_reason == "stop"
            assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test chat with API error"""
        with patch.object(provider.client.chat.completions, "create") as mock_create:
            mock_create.side_effect = Exception("API Error")

            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(Exception, match="API Error"):
                await provider.chat(messages)
