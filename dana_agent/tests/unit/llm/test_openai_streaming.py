"""Tests for OpenAI provider streaming and API detection."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from dana.common.llm.types import LLMMessage, LLMStreamChunk


# --- Helpers for building mock objects ---


def _make_chat_chunk(content=None, tool_calls=None, finish_reason=None):
    """Build a mock Chat Completions streaming chunk."""
    delta = MagicMock()
    delta.content = content
    delta.tool_calls = tool_calls

    choice = MagicMock()
    choice.delta = delta
    choice.finish_reason = finish_reason

    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


def _make_empty_chunk():
    """Build a mock chunk with empty choices."""
    chunk = MagicMock()
    chunk.choices = []
    return chunk


def _make_tool_call_delta(index, tc_id=None, name=None, arguments=None):
    """Build a mock incremental tool call delta."""
    tc = MagicMock()
    tc.index = index
    tc.id = tc_id

    if name or arguments:
        tc.function = MagicMock()
        tc.function.name = name
        tc.function.arguments = arguments
    else:
        tc.function = None

    return tc


def _make_responses_event(event_type, **kwargs):
    """Build a mock Responses API streaming event."""
    event = MagicMock()
    event.type = event_type
    for key, value in kwargs.items():
        setattr(event, key, value)
    return event


async def _async_iter(items):
    """Wrap a list as an async iterator."""
    for item in items:
        yield item


def _create_provider(model="gpt-4o", use_responses_api=None):
    """Create an OpenAICompatibleProvider with mocked client."""
    from dana.common.llm.providers.openai_compatible_base import OpenAICompatibleProvider

    provider = OpenAICompatibleProvider.__new__(OpenAICompatibleProvider)
    provider.model = model
    provider.client = MagicMock()
    provider._use_responses_api = use_responses_api
    return provider


# --- Chat Completions streaming tests ---


class TestStreamChatCompletions:
    """Test _stream_chat_completions() with mocked API."""

    @pytest.mark.asyncio
    async def test_text_stream_yields_text_deltas(self):
        provider = _create_provider()
        chunks = [
            _make_chat_chunk(content="Hello"),
            _make_chat_chunk(content=" world"),
            _make_chat_chunk(finish_reason="stop"),
        ]
        provider.client.chat.completions.create = AsyncMock(return_value=_async_iter(chunks))

        results = []
        async for chunk in provider._stream_chat_completions([LLMMessage(content="Hi", role="user")]):
            results.append(chunk)

        assert len(results) == 2
        assert results[0] == LLMStreamChunk(type="text_delta", content="Hello")
        assert results[1] == LLMStreamChunk(type="text_delta", content=" world")

    @pytest.mark.asyncio
    async def test_tool_call_stream_accumulates_deltas(self):
        provider = _create_provider()
        chunks = [
            _make_chat_chunk(tool_calls=[_make_tool_call_delta(0, tc_id="call_1", name="get_weather", arguments="")]),
            _make_chat_chunk(tool_calls=[_make_tool_call_delta(0, arguments='{"city":')]),
            _make_chat_chunk(tool_calls=[_make_tool_call_delta(0, arguments=' "Paris"}')]),
            _make_chat_chunk(finish_reason="tool_calls"),
        ]
        provider.client.chat.completions.create = AsyncMock(return_value=_async_iter(chunks))

        results = []
        async for chunk in provider._stream_chat_completions([LLMMessage(content="Weather?", role="user")]):
            results.append(chunk)

        assert len(results) == 1
        assert results[0].type == "tool_use"
        assert results[0].tool_call["id"] == "call_1"
        assert results[0].tool_call["name"] == "get_weather"
        assert results[0].tool_call["input"] == {"city": "Paris"}

    @pytest.mark.asyncio
    async def test_mixed_text_and_tool_calls(self):
        provider = _create_provider()
        chunks = [
            _make_chat_chunk(content="Let me check"),
            _make_chat_chunk(tool_calls=[_make_tool_call_delta(0, tc_id="call_1", name="search", arguments='{"q": "test"}')]),
            _make_chat_chunk(finish_reason="tool_calls"),
        ]
        provider.client.chat.completions.create = AsyncMock(return_value=_async_iter(chunks))

        results = []
        async for chunk in provider._stream_chat_completions([LLMMessage(content="Search", role="user")]):
            results.append(chunk)

        assert len(results) == 2
        assert results[0].type == "text_delta"
        assert results[1].type == "tool_use"

    @pytest.mark.asyncio
    async def test_empty_choices_skipped(self):
        provider = _create_provider()
        chunks = [_make_empty_chunk(), _make_chat_chunk(content="Hi"), _make_empty_chunk()]
        provider.client.chat.completions.create = AsyncMock(return_value=_async_iter(chunks))

        results = []
        async for chunk in provider._stream_chat_completions([LLMMessage(content="Hi", role="user")]):
            results.append(chunk)

        assert len(results) == 1
        assert results[0].content == "Hi"

    @pytest.mark.asyncio
    async def test_invalid_tool_args_json_yields_empty_dict(self):
        provider = _create_provider()
        chunks = [
            _make_chat_chunk(tool_calls=[_make_tool_call_delta(0, tc_id="call_1", name="bad", arguments="not json{")]),
            _make_chat_chunk(finish_reason="tool_calls"),
        ]
        provider.client.chat.completions.create = AsyncMock(return_value=_async_iter(chunks))

        results = []
        async for chunk in provider._stream_chat_completions([LLMMessage(content="x", role="user")]):
            results.append(chunk)

        assert results[0].tool_call["input"] == {}

    @pytest.mark.asyncio
    async def test_multiple_tool_calls(self):
        provider = _create_provider()
        chunks = [
            _make_chat_chunk(
                tool_calls=[
                    _make_tool_call_delta(0, tc_id="call_1", name="tool_a", arguments='{"a": 1}'),
                    _make_tool_call_delta(1, tc_id="call_2", name="tool_b", arguments='{"b": 2}'),
                ]
            ),
            _make_chat_chunk(finish_reason="tool_calls"),
        ]
        provider.client.chat.completions.create = AsyncMock(return_value=_async_iter(chunks))

        results = []
        async for chunk in provider._stream_chat_completions([LLMMessage(content="x", role="user")]):
            results.append(chunk)

        assert len(results) == 2
        names = {r.tool_call["name"] for r in results}
        assert names == {"tool_a", "tool_b"}

    @pytest.mark.asyncio
    async def test_post_loop_flush_on_stop_finish_reason(self):
        """Tool calls flushed even if finish_reason is 'stop' instead of 'tool_calls'."""
        provider = _create_provider()
        chunks = [
            _make_chat_chunk(tool_calls=[_make_tool_call_delta(0, tc_id="call_1", name="fn", arguments='{"x": 1}')]),
            _make_chat_chunk(finish_reason="stop"),
        ]
        provider.client.chat.completions.create = AsyncMock(return_value=_async_iter(chunks))

        results = []
        async for chunk in provider._stream_chat_completions([LLMMessage(content="x", role="user")]):
            results.append(chunk)

        assert len(results) == 1
        assert results[0].type == "tool_use"
        assert results[0].tool_call["input"] == {"x": 1}


# --- Responses API streaming tests ---


class TestStreamResponses:
    """Test _stream_responses() with mocked API."""

    @pytest.mark.asyncio
    async def test_text_delta_events(self):
        provider = _create_provider(model="gpt-5")
        events = [
            _make_responses_event("response.output_text.delta", delta="Hello"),
            _make_responses_event("response.output_text.delta", delta=" world"),
            _make_responses_event("response.completed"),
        ]
        provider.client.responses.create = AsyncMock(return_value=_async_iter(events))

        results = []
        async for chunk in provider._stream_responses([LLMMessage(content="Hi", role="user")]):
            results.append(chunk)

        assert len(results) == 2
        assert results[0] == LLMStreamChunk(type="text_delta", content="Hello")
        assert results[1] == LLMStreamChunk(type="text_delta", content=" world")

    @pytest.mark.asyncio
    async def test_tool_call_from_output_item_done(self):
        provider = _create_provider(model="gpt-5")
        item = MagicMock()
        item.type = "function_call"
        item.call_id = "call_resp_1"
        item.name = "get_weather"
        item.arguments = '{"city": "Tokyo"}'

        events = [_make_responses_event("response.output_item.done", item=item)]
        provider.client.responses.create = AsyncMock(return_value=_async_iter(events))

        results = []
        async for chunk in provider._stream_responses([LLMMessage(content="Weather?", role="user")]):
            results.append(chunk)

        assert len(results) == 1
        assert results[0].type == "tool_use"
        assert results[0].tool_call["id"] == "call_resp_1"
        assert results[0].tool_call["name"] == "get_weather"
        assert results[0].tool_call["input"] == {"city": "Tokyo"}

    @pytest.mark.asyncio
    async def test_reasoning_delta_yields_thinking(self):
        provider = _create_provider(model="o3")
        events = [_make_responses_event("response.reasoning.delta", delta="Let me think...")]
        provider.client.responses.create = AsyncMock(return_value=_async_iter(events))

        results = []
        async for chunk in provider._stream_responses([LLMMessage(content="Think", role="user")]):
            results.append(chunk)

        assert len(results) == 1
        assert results[0] == LLMStreamChunk(type="thinking", content="Let me think...")


# --- API detection tests ---


class TestAPIDetection:
    """Test _should_use_responses_api() routing logic."""

    def test_config_flag_true(self):
        provider = _create_provider(model="gpt-4o", use_responses_api=True)
        assert provider._should_use_responses_api() is True

    def test_config_flag_false(self):
        provider = _create_provider(model="gpt-5", use_responses_api=False)
        assert provider._should_use_responses_api() is False

    def test_gpt5_prefix_detection(self):
        provider = _create_provider(model="gpt-5-mini")
        assert provider._should_use_responses_api() is True

    def test_o3_prefix_detection(self):
        provider = _create_provider(model="o3-mini")
        assert provider._should_use_responses_api() is True

    def test_o4_prefix_detection(self):
        provider = _create_provider(model="o4-preview")
        assert provider._should_use_responses_api() is True

    def test_gpt4o_defaults_chat_completions(self):
        provider = _create_provider(model="gpt-4o")
        assert provider._should_use_responses_api() is False

    def test_unknown_model_defaults_chat_completions(self):
        provider = _create_provider(model="some-custom-model")
        assert provider._should_use_responses_api() is False

    def test_gpt35_defaults_chat_completions(self):
        provider = _create_provider(model="gpt-3.5-turbo")
        assert provider._should_use_responses_api() is False
