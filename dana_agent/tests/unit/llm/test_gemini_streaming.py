"""Tests for Gemini provider chat and streaming."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dana.common.llm.types import LLMMessage


# --- Helpers ---


def _make_text_part(text):
    """Build a mock Part with text."""
    part = MagicMock()
    part.text = text
    part.function_call = None
    return part


def _make_function_call_part(name, args):
    """Build a mock Part with function_call."""
    part = MagicMock()
    part.text = None
    part.function_call = MagicMock()
    part.function_call.name = name
    part.function_call.args = args
    return part


def _make_response(parts, prompt_tokens=10, completion_tokens=5, total_tokens=15, finish_reason="STOP"):
    """Build a mock GenerateContentResponse."""
    candidate = MagicMock()
    candidate.content = MagicMock()
    candidate.content.parts = parts
    candidate.finish_reason = finish_reason

    response = MagicMock()
    response.candidates = [candidate]
    response.usage_metadata = MagicMock()
    response.usage_metadata.prompt_token_count = prompt_tokens
    response.usage_metadata.candidates_token_count = completion_tokens
    response.usage_metadata.total_token_count = total_tokens
    return response


def _make_stream_chunk(parts):
    """Build a mock streaming chunk."""
    candidate = MagicMock()
    candidate.content = MagicMock()
    candidate.content.parts = parts

    chunk = MagicMock()
    chunk.candidates = [candidate]
    return chunk


async def _async_iter(items):
    """Wrap a list as an async iterator."""
    for item in items:
        yield item


@pytest.fixture
def provider():
    """Create GeminiProvider with mocked client."""
    with patch("dana.common.llm.providers.gemini.genai"):
        from dana.common.llm.providers.gemini import GeminiProvider

        return GeminiProvider(api_key="test-key", model="gemini-2.5-flash")


# --- Chat tests ---


class TestGeminiChat:
    """Tests for GeminiProvider.chat()."""

    @pytest.mark.asyncio
    async def test_chat_text_response(self, provider):
        """Test basic text response from chat."""
        mock_response = _make_response([_make_text_part("Hello from Gemini!")])

        provider.client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        messages = [LLMMessage(role="user", content="Hello")]
        response = await provider.chat(messages)

        assert response.content == "Hello from Gemini!"
        assert response.model == "gemini-2.5-flash"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 5

    @pytest.mark.asyncio
    async def test_chat_with_tool_calls(self, provider):
        """Test chat response with function calls."""
        parts = [_make_function_call_part("get_weather", {"city": "Paris"})]
        mock_response = _make_response(parts)

        provider.client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        messages = [LLMMessage(role="user", content="Weather in Paris?")]
        response = await provider.chat(messages)

        assert response.content == ""
        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].function.name == "get_weather"
        assert json.loads(response.tool_calls[0].function.arguments) == {"city": "Paris"}

    @pytest.mark.asyncio
    async def test_chat_with_system_message(self, provider):
        """Test that system messages are extracted as system_instruction."""
        mock_response = _make_response([_make_text_part("I am helpful.")])
        provider.client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        messages = [
            LLMMessage(role="system", content="You are helpful."),
            LLMMessage(role="user", content="Hi"),
        ]
        await provider.chat(messages)

        call_kwargs = provider.client.aio.models.generate_content.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
        assert config.system_instruction == "You are helpful."

    @pytest.mark.asyncio
    async def test_chat_api_error(self, provider):
        """Test error propagation."""
        provider.client.aio.models.generate_content = AsyncMock(side_effect=Exception("Gemini API Error"))

        messages = [LLMMessage(role="user", content="Test")]
        with pytest.raises(Exception, match="Gemini API Error"):
            await provider.chat(messages)


# --- Stream tests ---


class TestGeminiStream:
    """Tests for GeminiProvider.stream()."""

    @pytest.mark.asyncio
    async def test_stream_text_deltas(self, provider):
        """Test streaming text chunks."""
        chunks = [
            _make_stream_chunk([_make_text_part("Hello ")]),
            _make_stream_chunk([_make_text_part("world!")]),
        ]
        provider.client.aio.models.generate_content_stream = AsyncMock(return_value=_async_iter(chunks))

        messages = [LLMMessage(role="user", content="Hi")]
        collected = []
        async for chunk in provider.stream(messages):
            collected.append(chunk)

        assert len(collected) == 2
        assert collected[0].type == "text_delta"
        assert collected[0].content == "Hello "
        assert collected[1].type == "text_delta"
        assert collected[1].content == "world!"

    @pytest.mark.asyncio
    async def test_stream_tool_call(self, provider):
        """Test streaming with function call in final chunk."""
        chunks = [
            _make_stream_chunk([_make_text_part("Let me check.")]),
            _make_stream_chunk([_make_function_call_part("search", {"q": "test"})]),
        ]
        provider.client.aio.models.generate_content_stream = AsyncMock(return_value=_async_iter(chunks))

        messages = [LLMMessage(role="user", content="Search for test")]
        collected = []
        async for chunk in provider.stream(messages):
            collected.append(chunk)

        assert len(collected) == 2
        assert collected[0].type == "text_delta"
        assert collected[1].type == "tool_use"
        assert collected[1].tool_call["name"] == "search"
        assert collected[1].tool_call["input"] == {"q": "test"}

    @pytest.mark.asyncio
    async def test_stream_empty_candidates_skipped(self, provider):
        """Test that chunks with no candidates are skipped."""
        empty_chunk = MagicMock()
        empty_chunk.candidates = []
        text_chunk = _make_stream_chunk([_make_text_part("Hello")])

        provider.client.aio.models.generate_content_stream = AsyncMock(return_value=_async_iter([empty_chunk, text_chunk]))

        messages = [LLMMessage(role="user", content="Hi")]
        collected = []
        async for chunk in provider.stream(messages):
            collected.append(chunk)

        assert len(collected) == 1
        assert collected[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_stream_error(self, provider):
        """Test error propagation during streaming."""

        async def failing_stream(*args, **kwargs):
            yield _make_stream_chunk([_make_text_part("start")])
            raise Exception("Stream interrupted")

        provider.client.aio.models.generate_content_stream = AsyncMock(return_value=failing_stream())

        messages = [LLMMessage(role="user", content="Hi")]
        with pytest.raises(Exception, match="Stream interrupted"):
            async for _ in provider.stream(messages):
                pass


# --- Message conversion tests ---


class TestGeminiMessageConversion:
    """Tests for _convert_messages()."""

    def _convert(self, messages):
        from unittest.mock import patch as _patch

        with _patch("dana.common.llm.providers.gemini.genai"):
            from dana.common.llm.providers.gemini import GeminiProvider

            p = GeminiProvider(api_key="test-key")
            return p.prepare_messages(messages)

    def test_system_message_extracted(self):
        """System messages become system_instruction."""
        msgs = [
            LLMMessage(role="system", content="Be helpful."),
            LLMMessage(role="user", content="Hi"),
        ]
        system, contents = self._convert(msgs)
        assert system == "Be helpful."
        assert len(contents) == 1
        assert contents[0].role == "user"

    def test_multiple_system_messages_joined(self):
        """Multiple system messages joined with double newline."""
        msgs = [
            LLMMessage(role="system", content="Rule 1"),
            LLMMessage(role="system", content="Rule 2"),
            LLMMessage(role="user", content="Hi"),
        ]
        system, _ = self._convert(msgs)
        assert system == "Rule 1\n\nRule 2"

    def test_assistant_role_mapped_to_model(self):
        """Assistant role maps to 'model' in Gemini."""
        msgs = [LLMMessage(role="assistant", content="Hello")]
        _, contents = self._convert(msgs)
        assert contents[0].role == "model"

    def test_tool_result_mapped_to_function_response(self):
        """Tool results become FunctionResponse parts."""
        msgs = [
            LLMMessage(
                role="assistant",
                content="",
                tool_calls=[{"id": "c1", "name": "search", "arguments": {"q": "test"}}],
            ),
            LLMMessage(role="tool", content='{"answer": 42}', tool_call_id="c1"),
        ]
        _, contents = self._convert(msgs)
        # Tool result should be user role with function_response part
        tool_content = contents[1]
        assert tool_content.role == "user"
        assert tool_content.parts[0].function_response is not None


# --- Tool conversion tests ---


class TestGeminiToolConversion:
    """Tests for _convert_tools()."""

    def _convert(self, tools):
        from unittest.mock import patch as _patch

        with _patch("dana.common.llm.providers.gemini.genai"):
            from dana.common.llm.providers.gemini import GeminiProvider

            p = GeminiProvider(api_key="test-key")
            return p.prepare_tools(tools)

    def test_openai_format_dict(self):
        """OpenAI-style dict tools are converted."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {"type": "object", "properties": {"city": {"type": "string"}}},
                },
            }
        ]
        result = self._convert(tools)
        assert len(result) == 1
        decls = result[0].function_declarations
        assert len(decls) == 1
        assert decls[0].name == "get_weather"
