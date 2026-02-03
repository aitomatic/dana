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


class TestOpenAIModelCompatibility:
    """Unit tests for OpenAI model-specific parameter filtering."""

    def test_get_model_family_gpt5_mini(self):
        """Test that gpt-5-mini is recognized as gpt-5 family."""
        from dana.common.llm.providers.openai import OpenAIProvider

        assert OpenAIProvider._get_model_family("gpt-5-mini") == "gpt-5"

    def test_get_model_family_gpt5_turbo(self):
        """Test that gpt-5-turbo is recognized as gpt-5 family."""
        from dana.common.llm.providers.openai import OpenAIProvider

        assert OpenAIProvider._get_model_family("gpt-5-turbo") == "gpt-5"

    def test_get_model_family_gpt5_exact(self):
        """Test that exact gpt-5 match works."""
        from dana.common.llm.providers.openai import OpenAIProvider

        assert OpenAIProvider._get_model_family("gpt-5") == "gpt-5"

    def test_get_model_family_gpt4o_no_match(self):
        """Test that gpt-4o is not matched (no restrictions)."""
        from dana.common.llm.providers.openai import OpenAIProvider

        assert OpenAIProvider._get_model_family("gpt-4o") is None

    def test_get_model_family_gpt4_no_match(self):
        """Test that gpt-4 is not matched (no restrictions)."""
        from dana.common.llm.providers.openai import OpenAIProvider

        assert OpenAIProvider._get_model_family("gpt-4") is None

    def test_get_model_family_gpt50_no_match(self):
        """Test that gpt-50 is NOT matched as gpt-5 (boundary check)."""
        from dana.common.llm.providers.openai import OpenAIProvider

        # gpt-50 should NOT match gpt-5 (50 != 5-)
        assert OpenAIProvider._get_model_family("gpt-50") is None

    def test_filter_params_removes_temperature_zero_for_gpt5(self):
        """Test that temperature=0 is removed for gpt-5 models."""
        from dana.common.llm.providers.openai import OpenAIProvider

        params = {"temperature": 0, "max_tokens": 100}
        filtered = OpenAIProvider._filter_params_for_model("gpt-5-mini", params)

        assert "temperature" not in filtered
        assert filtered["max_tokens"] == 100

    def test_filter_params_keeps_temperature_one_for_gpt5(self):
        """Test that temperature=1 is kept for gpt-5 models."""
        from dana.common.llm.providers.openai import OpenAIProvider

        params = {"temperature": 1, "max_tokens": 100}
        filtered = OpenAIProvider._filter_params_for_model("gpt-5-mini", params)

        assert filtered["temperature"] == 1
        assert filtered["max_tokens"] == 100

    def test_filter_params_removes_temperature_half_for_gpt5(self):
        """Test that temperature=0.5 is removed for gpt-5 models."""
        from dana.common.llm.providers.openai import OpenAIProvider

        params = {"temperature": 0.5}
        filtered = OpenAIProvider._filter_params_for_model("gpt-5-mini", params)

        assert "temperature" not in filtered

    def test_filter_params_unchanged_for_gpt4(self):
        """Test that params are unchanged for gpt-4 models."""
        from dana.common.llm.providers.openai import OpenAIProvider

        params = {"temperature": 0, "max_tokens": 100}
        filtered = OpenAIProvider._filter_params_for_model("gpt-4o", params)

        assert filtered["temperature"] == 0
        assert filtered["max_tokens"] == 100

    def test_filter_params_does_not_mutate_original(self):
        """Test that original params dict is not mutated."""
        from dana.common.llm.providers.openai import OpenAIProvider

        params = {"temperature": 0, "max_tokens": 100}
        OpenAIProvider._filter_params_for_model("gpt-5-mini", params)

        # Original should be unchanged
        assert params["temperature"] == 0
        assert params["max_tokens"] == 100


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
        with patch("dana.common.llm.providers.azure.AsyncAzureOpenAI"):
            from dana.common.llm.providers.azure import AzureProvider

            return AzureProvider(
                api_key="test-key", base_url="https://test.openai.azure.com/", api_version="2024-02-15-preview", model="gpt-35-turbo"
            )

    def test_init(self, provider):
        """Test AzureProvider initialization"""
        assert provider.api_key == "test-key"
        assert provider.api_version == "2024-02-15-preview"
        assert provider.model == "gpt-35-turbo"
        assert provider.deployment_name == "gpt-35-turbo"

    def test_supports_native_tools(self, provider):
        """Test that Azure provider supports native tools"""
        assert provider.supports_native_tools is True

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello from Azure!"
        mock_response.choices[0].message.tool_calls = None
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
            assert response.tool_calls is None

    @pytest.mark.asyncio
    async def test_chat_with_tool_calls(self, provider):
        """Test chat with native tool calls in response"""
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "get_weather"
        mock_tool_call.function.arguments = '{"location": "Paris"}'

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = ""
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.model = "gpt-35-turbo"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 15
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 25

        # Create an async mock for the create method
        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            tools = [{"type": "function", "function": {"name": "get_weather", "parameters": {}}}]
            messages = [LLMMessage(role="user", content="What's the weather in Paris?")]
            response = await provider.chat(messages, tools=tools)

            assert isinstance(response, LLMResponse)
            assert response.content == ""
            assert response.finish_reason == "tool_calls"
            assert response.tool_calls is not None
            assert len(response.tool_calls) == 1

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
