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


class TestOpenAIReasoningTokens:
    """Unit tests for OpenAI reasoning tokens parsing (thinking models)"""

    @pytest.fixture
    def provider(self):
        """Create OpenAIProvider instance for testing"""
        with patch("dana.common.llm.providers.openai.AsyncOpenAI"):
            from dana.common.llm.providers.openai import OpenAIProvider

            return OpenAIProvider(api_key="test-key", model="gpt-5-thinking-mini")

    @pytest.mark.asyncio
    async def test_chat_with_reasoning_tokens(self, provider):
        """Test that reasoning_tokens are parsed from thinking model response"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "The answer is 42"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-5-thinking-mini"

        # Mock usage with completion_tokens_details containing reasoning_tokens
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 200
        mock_response.usage.total_tokens = 250
        mock_response.usage.prompt_tokens_details = None

        # This is the key part - completion_tokens_details with reasoning_tokens
        mock_completion_details = Mock()
        mock_completion_details.reasoning_tokens = 150
        mock_response.usage.completion_tokens_details = mock_completion_details

        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="What is the meaning of life?")]
            response = await provider.chat(messages)

            assert isinstance(response, LLMResponse)
            assert response.content == "The answer is 42"
            assert response.model == "gpt-5-thinking-mini"
            assert response.reasoning_tokens == 150

    @pytest.mark.asyncio
    async def test_chat_without_reasoning_tokens(self, provider):
        """Test that reasoning_tokens is None for non-thinking models"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.usage.prompt_tokens_details = None
        mock_response.usage.completion_tokens_details = None  # No reasoning details

        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Hello")]
            response = await provider.chat(messages)

            assert response.reasoning_tokens is None

    @pytest.mark.asyncio
    async def test_chat_with_zero_reasoning_tokens(self, provider):
        """Test that zero reasoning_tokens is treated as None (falsy)"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Quick response"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-5-thinking-mini"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.usage.prompt_tokens_details = None

        # Zero reasoning tokens (model didn't use thinking)
        mock_completion_details = Mock()
        mock_completion_details.reasoning_tokens = 0
        mock_response.usage.completion_tokens_details = mock_completion_details

        async def mock_create(*args, **kwargs):
            return mock_response

        with patch.object(provider.client.chat.completions, "create", side_effect=mock_create):
            messages = [LLMMessage(role="user", content="Hi")]
            response = await provider.chat(messages)

            # Zero is falsy, so reasoning_tokens should be None
            assert response.reasoning_tokens is None


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

    def test_init_with_base_url_parameter(self):
        """Test AnthropicProvider initialization with explicit base_url parameter"""
        with patch("dana.common.llm.providers.anthropic.anthropic") as mock_anthropic:
            from dana.common.llm.providers.anthropic import AnthropicProvider

            provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet", base_url="https://custom.api.com")
            assert provider.base_url == "https://custom.api.com"
            # Verify AsyncAnthropic was called with the base_url
            mock_anthropic.AsyncAnthropic.assert_called_once()
            call_kwargs = mock_anthropic.AsyncAnthropic.call_args[1]
            assert call_kwargs["base_url"] == "https://custom.api.com"

    def test_init_with_base_url_env_var(self):
        """Test AnthropicProvider initialization with ANTHROPIC_BASE_URL env var"""
        with patch("dana.common.llm.providers.anthropic.anthropic") as mock_anthropic:
            with patch("dana.common.config.os.getenv") as mock_getenv:
                # Mock getenv to return our custom URL for ANTHROPIC_BASE_URL
                def getenv_side_effect(key, default=None):
                    if key == "ANTHROPIC_BASE_URL":
                        return "https://env-custom.api.com"
                    if key == "ANTHROPIC_API_KEY":
                        return None
                    return default

                mock_getenv.side_effect = getenv_side_effect

                from dana.common.llm.providers.anthropic import AnthropicProvider

                provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet")
                assert provider.base_url == "https://env-custom.api.com"
                # Verify AsyncAnthropic was called with the base_url from env
                call_kwargs = mock_anthropic.AsyncAnthropic.call_args[1]
                assert call_kwargs["base_url"] == "https://env-custom.api.com"

    def test_init_without_base_url(self):
        """Test AnthropicProvider initialization without base_url uses default"""
        with patch("dana.common.llm.providers.anthropic.anthropic") as mock_anthropic:
            from dana.common.llm.providers.anthropic import AnthropicProvider

            AnthropicProvider(api_key="test-key", model="claude-3-sonnet")
            # base_url should be the default from config (https://api.anthropic.com)
            # or None if env var not set - either way, client should work
            mock_anthropic.AsyncAnthropic.assert_called_once()

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
        mock_response.usage.prompt_tokens_details = None
        mock_response.usage.completion_tokens_details = None

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


class TestGeminiProvider:
    """Unit tests for Gemini provider"""

    @pytest.fixture
    def provider(self):
        """Create GeminiProvider instance for testing"""
        with patch("dana.common.llm.providers.gemini.genai"):
            from dana.common.llm.providers.gemini import GeminiProvider

            return GeminiProvider(api_key="test-key", model="gemini-2.5-flash")

    def test_init(self, provider):
        """Test GeminiProvider initialization"""
        assert provider.api_key == "test-key"
        assert provider.model == "gemini-2.5-flash"

    def test_supports_native_tools(self, provider):
        """Test that Gemini provider supports native tools"""
        assert provider.supports_native_tools is True

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """Test successful chat completion"""
        from unittest.mock import AsyncMock, MagicMock

        mock_part = MagicMock()
        mock_part.text = "Hello from Gemini!"
        mock_part.function_call = None

        mock_candidate = MagicMock()
        mock_candidate.content = MagicMock()
        mock_candidate.content.parts = [mock_part]
        mock_candidate.finish_reason = "STOP"

        mock_response = MagicMock()
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 5
        mock_response.usage_metadata.total_token_count = 15

        provider.client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        messages = [LLMMessage(role="user", content="Hello")]
        response = await provider.chat(messages)

        assert isinstance(response, LLMResponse)
        assert response.content == "Hello from Gemini!"
        assert response.model == "gemini-2.5-flash"
        assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test chat with API error"""
        from unittest.mock import AsyncMock

        provider.client.aio.models.generate_content = AsyncMock(side_effect=Exception("Gemini API Error"))

        messages = [LLMMessage(role="user", content="Test")]

        with pytest.raises(Exception, match="Gemini API Error"):
            await provider.chat(messages)


class TestAnthropicMessageConversion:
    """Unit tests for prepare_anthropic_messages() — pure function, no mocking needed."""

    def _prepare(self, messages):
        from dana.common.llm.providers.anthropic import prepare_anthropic_messages

        return prepare_anthropic_messages(messages)

    # --- Bug 1: Tool call field name mismatch ---

    def test_tool_calls_runtime_format(self):
        """Runtime format uses 'function' and 'tool_call_id' keys."""
        msgs = [
            LLMMessage(
                role="assistant",
                content="",
                tool_calls=[
                    {"function": "get_weather", "tool_call_id": "call_abc", "arguments": {"city": "Paris"}},
                ],
            ),
        ]
        system, out = self._prepare(msgs)
        block = out[0]["content"][0]
        assert block["type"] == "tool_use"
        assert block["id"] == "call_abc"
        assert block["name"] == "get_weather"
        assert block["input"] == {"city": "Paris"}

    def test_tool_calls_native_format(self):
        """Native format uses 'id' and 'name' keys."""
        msgs = [
            LLMMessage(
                role="assistant",
                content="",
                tool_calls=[
                    {"id": "call_xyz", "name": "search", "arguments": {"q": "test"}},
                ],
            ),
        ]
        system, out = self._prepare(msgs)
        block = out[0]["content"][0]
        assert block["id"] == "call_xyz"
        assert block["name"] == "search"

    def test_tool_calls_mixed_formats(self):
        """Both formats in one message resolve correctly."""
        msgs = [
            LLMMessage(
                role="assistant",
                content="thinking...",
                tool_calls=[
                    {"function": "func_a", "tool_call_id": "id_1", "arguments": {}},
                    {"id": "id_2", "name": "func_b", "arguments": {}},
                ],
            ),
        ]
        system, out = self._prepare(msgs)
        blocks = out[0]["content"]
        assert blocks[0] == {"type": "text", "text": "thinking..."}
        assert blocks[1]["id"] == "id_1"
        assert blocks[1]["name"] == "func_a"
        assert blocks[2]["id"] == "id_2"
        assert blocks[2]["name"] == "func_b"

    # --- Bug 2: Multiple system messages ---

    def test_single_system_message(self):
        """One system msg without cache_control → plain string."""
        msgs = [
            LLMMessage(role="system", content="You are helpful."),
            LLMMessage(role="user", content="Hi"),
        ]
        system, out = self._prepare(msgs)
        assert system == "You are helpful."
        assert len(out) == 1

    def test_single_system_message_with_cache_control(self):
        """One system msg with cache_control → list with one block."""
        cc = {"type": "ephemeral"}
        msgs = [
            LLMMessage(role="system", content="You are helpful.", cache_control=cc),
            LLMMessage(role="user", content="Hi"),
        ]
        system, out = self._prepare(msgs)
        assert isinstance(system, list)
        assert len(system) == 1
        assert system[0]["text"] == "You are helpful."
        assert system[0]["cache_control"] == cc

    def test_multiple_system_messages_accumulated(self):
        """Two system msgs → list of 2 content blocks."""
        msgs = [
            LLMMessage(role="system", content="You are an agent."),
            LLMMessage(role="system", content="Current time: 2025-01-01"),
            LLMMessage(role="user", content="Hi"),
        ]
        system, out = self._prepare(msgs)
        assert isinstance(system, list)
        assert len(system) == 2
        assert system[0]["text"] == "You are an agent."
        assert system[1]["text"] == "Current time: 2025-01-01"

    def test_multiple_system_messages_with_cache_control(self):
        """cache_control preserved on the block that has it."""
        cc = {"type": "ephemeral"}
        msgs = [
            LLMMessage(role="system", content="Agent prompt", cache_control=cc),
            LLMMessage(role="system", content="Context info"),
            LLMMessage(role="user", content="Hi"),
        ]
        system, out = self._prepare(msgs)
        assert isinstance(system, list)
        assert system[0]["cache_control"] == cc
        assert "cache_control" not in system[1]

    # --- Bug 3: Consecutive same-role merging ---

    def test_consecutive_user_messages_merged(self):
        """Two user msgs → one user msg with merged content blocks."""
        msgs = [
            LLMMessage(role="user", content="First part."),
            LLMMessage(role="user", content="Second part."),
        ]
        system, out = self._prepare(msgs)
        assert len(out) == 1
        assert out[0]["role"] == "user"
        # Content must be a list of blocks after merging
        assert isinstance(out[0]["content"], list)
        texts = [b["text"] for b in out[0]["content"]]
        assert texts == ["First part.", "Second part."]

    def test_consecutive_assistant_text_messages_merged(self):
        """Two text-only assistant msgs → merged into one."""
        msgs = [
            LLMMessage(role="assistant", content="Part A"),
            LLMMessage(role="assistant", content="Part B"),
        ]
        system, out = self._prepare(msgs)
        assert len(out) == 1
        assert out[0]["role"] == "assistant"

    def test_assistant_text_then_tool_calls_merged(self):
        """Assistant text + assistant tool_calls → one msg with text + tool_use blocks."""
        msgs = [
            LLMMessage(role="assistant", content="Let me check."),
            LLMMessage(
                role="assistant",
                content="",
                tool_calls=[
                    {"id": "c1", "name": "search", "arguments": {"q": "test"}},
                ],
            ),
        ]
        system, out = self._prepare(msgs)
        assert len(out) == 1
        assert out[0]["role"] == "assistant"
        blocks = out[0]["content"]
        types = [b["type"] for b in blocks]
        assert "text" in types
        assert "tool_use" in types

    def test_tool_result_followed_by_user_text_merged(self):
        """Tool result (user) + regular user msg → merged, no consecutive same roles."""
        msgs = [
            LLMMessage(role="tool", content="42", tool_call_id="c1"),
            LLMMessage(role="user", content="Thanks, now explain."),
        ]
        system, out = self._prepare(msgs)
        # Both become user role; should be merged
        assert len(out) == 1
        assert out[0]["role"] == "user"

    # --- No-regression tests ---

    def test_parallel_tool_results_grouped(self):
        """Two consecutive tool results → one user msg with 2 tool_result blocks."""
        msgs = [
            LLMMessage(role="tool", content="result1", tool_call_id="c1"),
            LLMMessage(role="tool", content="result2", tool_call_id="c2"),
        ]
        system, out = self._prepare(msgs)
        assert len(out) == 1
        assert out[0]["role"] == "user"
        tool_results = [b for b in out[0]["content"] if b["type"] == "tool_result"]
        assert len(tool_results) == 2

    def test_user_message_cache_control_preserved(self):
        """cache_control on user msg → content blocks format preserved."""
        cc = {"type": "ephemeral"}
        msgs = [
            LLMMessage(role="user", content="Hello", cache_control=cc),
        ]
        system, out = self._prepare(msgs)
        assert isinstance(out[0]["content"], list)
        assert out[0]["content"][0]["cache_control"] == cc

    def test_no_system_in_output_messages(self):
        """System msgs excluded from output messages list."""
        msgs = [
            LLMMessage(role="system", content="sys"),
            LLMMessage(role="user", content="hi"),
            LLMMessage(role="assistant", content="hello"),
        ]
        system, out = self._prepare(msgs)
        roles = [m["role"] for m in out]
        assert "system" not in roles

    def test_empty_messages(self):
        """Empty input → (None, [])."""
        system, out = self._prepare([])
        assert system is None
        assert out == []
