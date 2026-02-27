"""
Unit tests for STARAgent streaming: call_llm_stream(), aquery_stream().
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dana.common.llm.types import LLMMessage, LLMResponse
from dana.core.llm.llm_caller import LLMCaller
from dana.core.runtime.protocols import StreamEvent, StreamEventType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(content: str = "Hello, world!") -> LLMResponse:
    return LLMResponse(content=content, model="test-model")


def _make_agent():
    """Create a minimal STARAgent without registry or LLM side-effects."""
    from dana.core.agent.star_agent import STARAgent

    return STARAgent(
        agent_type="test-agent",
        auto_register=False,
        enable_skills=False,
        enable_web_search=False,
        enable_code_execution=False,
        enable_assistant=False,
        compress_timeline=False,
    )


async def _collect_stream(agen) -> list[StreamEvent]:
    """Collect all events from an async generator into a list."""
    events: list[StreamEvent] = []
    async for event in agen:
        events.append(event)
    return events


# ---------------------------------------------------------------------------
# LLMCaller.call_llm_stream()
# ---------------------------------------------------------------------------


class TestCallLlmStream:
    """Tests for LLMCaller.call_llm_stream()."""

    @pytest.mark.asyncio
    async def test_yields_chunks_from_llm_stream(self):
        """Should yield each text chunk from the underlying LLM stream."""

        async def _fake_stream(messages, **kwargs):
            for chunk in ["Hello", ", ", "world", "!"]:
                yield chunk

        mock_llm = MagicMock()
        mock_llm.stream = _fake_stream
        caller = LLMCaller(llm=mock_llm)

        chunks = []
        async for chunk in caller.call_llm_stream([LLMMessage(role="user", content="hi")]):
            chunks.append(chunk)

        assert chunks == ["Hello", ", ", "world", "!"]

    @pytest.mark.asyncio
    async def test_passes_agent_info_to_llm_stream(self):
        """Should forward agent_id and agent_type to llm.stream()."""
        received_kwargs: dict = {}

        async def _fake_stream(messages, **kwargs):
            received_kwargs.update(kwargs)
            yield "ok"

        mock_llm = MagicMock()
        mock_llm.stream = _fake_stream

        mock_agent = MagicMock()
        mock_agent.object_id = "agent-123"
        mock_agent.agent_type = "test"

        caller = LLMCaller(llm=mock_llm, agent_getter=lambda: mock_agent)

        async for _ in caller.call_llm_stream([LLMMessage(role="user", content="hi")]):
            pass

        assert received_kwargs.get("agent_id") == "agent-123"
        assert received_kwargs.get("agent_type") == "test"

    @pytest.mark.asyncio
    async def test_empty_stream_yields_nothing(self):
        """If the LLM stream yields nothing, call_llm_stream should be empty."""

        async def _empty_stream(messages, **kwargs):
            return
            yield  # makes it an async generator

        mock_llm = MagicMock()
        mock_llm.stream = _empty_stream
        caller = LLMCaller(llm=mock_llm)

        chunks = []
        async for chunk in caller.call_llm_stream([]):
            chunks.append(chunk)

        assert chunks == []


# ---------------------------------------------------------------------------
# STARAgent.aquery_stream() — basic TEXT_DELTA + DONE flow
# ---------------------------------------------------------------------------


class TestAqueryStreamBasic:
    """aquery_stream() yields TEXT_DELTA events then a DONE event."""

    @pytest.mark.asyncio
    async def test_yields_text_delta_then_done(self):
        """A simple text-only response should produce TEXT_DELTA(s) + DONE."""
        agent = _make_agent()

        # Mock the think_stream to yield one TEXT_DELTA and set result_holder
        async def _mock_think_stream(trace_percepts, result_holder):
            yield StreamEvent(
                event_type=StreamEventType.TEXT_DELTA,
                data="Hello, world!",
                iteration=1,
            )
            # Populate the result holder so _run_aquery_stream can continue
            from dana.core.agent.base_star_agent import EXIT_STAR_LOOP_FLAG

            result_holder["trace_thoughts"] = {
                "trace_thoughts": {
                    "response": "Hello, world!",
                    "tool_calls": [],
                    "done": True,
                    EXIT_STAR_LOOP_FLAG: True,
                }
            }

        # Mock _act_async to return exit signal immediately
        async def _mock_act_async(trace_thoughts):
            from dana.core.agent.base_star_agent import EXIT_STAR_LOOP_FLAG

            return {"trace_outputs": {EXIT_STAR_LOOP_FLAG: True}}

        with patch.object(agent, "_think_stream", _mock_think_stream), patch.object(agent, "_act_async", _mock_act_async):
            events = await _collect_stream(agent.aquery_stream(message="hello"))

        event_types = [e.event_type for e in events]
        assert StreamEventType.TEXT_DELTA in event_types
        assert events[-1].event_type == StreamEventType.DONE

    @pytest.mark.asyncio
    async def test_yields_tool_call_start_and_tool_result(self):
        """Should yield TOOL_CALL_START before tool execution and TOOL_RESULT after."""
        agent = _make_agent()

        tool_calls = [{"function": "search:web", "arguments": {"query": "python"}}]
        tool_results = [{"type": "resource", "result": "some results"}]

        # First iteration: think yields tool calls
        call_count = {"n": 0}

        async def _mock_think_stream(trace_percepts, result_holder):
            from dana.core.agent.base_star_agent import EXIT_STAR_LOOP_FLAG

            call_count["n"] += 1
            yield StreamEvent(
                event_type=StreamEventType.TEXT_DELTA,
                data="Let me search...",
                iteration=1,
            )
            if call_count["n"] == 1:
                # First call: signal tool calls
                result_holder["trace_thoughts"] = {
                    "trace_thoughts": {
                        "response": "",
                        "tool_calls": tool_calls,
                        "done": False,
                    }
                }
            else:
                # Second call: signal done
                result_holder["trace_thoughts"] = {
                    "trace_thoughts": {
                        "response": "Found results",
                        "tool_calls": [],
                        "done": True,
                        EXIT_STAR_LOOP_FLAG: True,
                    }
                }

        async def _mock_act_async(trace_thoughts):
            from dana.core.agent.base_star_agent import EXIT_STAR_LOOP_FLAG

            tcs = trace_thoughts.get("tool_calls", [])
            if tcs:
                return {
                    "trace_outputs": {
                        "tool_results": tool_results,
                        "tool_calls": tcs,
                        "response": "",
                    }
                }
            return {"trace_outputs": {EXIT_STAR_LOOP_FLAG: True}}

        with patch.object(agent, "_think_stream", _mock_think_stream), patch.object(agent, "_act_async", _mock_act_async):
            events = await _collect_stream(agent.aquery_stream(message="search python"))

        event_types = [e.event_type for e in events]
        assert StreamEventType.TOOL_CALL_START in event_types
        assert StreamEventType.TOOL_RESULT in event_types
        assert events[-1].event_type == StreamEventType.DONE

    @pytest.mark.asyncio
    async def test_yields_error_event_on_exception(self):
        """When _think_stream raises, aquery_stream should yield ERROR."""
        agent = _make_agent()

        async def _mock_think_stream_error(trace_percepts, result_holder):
            raise RuntimeError("LLM failed")
            yield  # make it an async generator

        async def _mock_act_async(trace_thoughts):
            from dana.core.agent.base_star_agent import EXIT_STAR_LOOP_FLAG

            return {"trace_outputs": {EXIT_STAR_LOOP_FLAG: True}}

        with patch.object(agent, "_think_stream", _mock_think_stream_error), patch.object(agent, "_act_async", _mock_act_async):
            events = await _collect_stream(agent.aquery_stream(message="hello"))

        assert any(e.event_type == StreamEventType.ERROR for e in events)
        # Should NOT have DONE after error (loop exits)
        error_idx = next(i for i, e in enumerate(events) if e.event_type == StreamEventType.ERROR)
        assert error_idx == len(events) - 1  # ERROR is the last event


# ---------------------------------------------------------------------------
# _think_stream() integration-style test (no real LLM calls)
# ---------------------------------------------------------------------------


class TestThinkStream:
    """Tests for STARAgent._think_stream() with a mocked LLM stream."""

    @pytest.mark.asyncio
    async def test_buffers_chunks_and_populates_result_holder(self):
        """TEXT_DELTA events should contain each chunk; result_holder gets the parsed trace."""
        agent = _make_agent()

        # Mock the runtime's LLM caller stream
        async def _fake_call_llm_stream(messages):
            for chunk in ["<done>true</done>", "<response>Hi!</response>"]:
                yield chunk

        # Mock runtime to provide call_llm_stream and parse_response
        mock_runtime = MagicMock()
        mock_runtime.build_prompt.return_value = []
        mock_runtime._llm_caller = MagicMock()
        mock_runtime._llm_caller.call_llm_stream = _fake_call_llm_stream

        # parse_response returns a simple ParsedResponse
        from dana.core.runtime.protocols import ParsedResponse

        mock_runtime.parse_response.return_value = ParsedResponse(
            done=True,
            response="Hi!",
            reasoning=None,
            tool_calls=[],
            todo_list=None,
        )
        mock_runtime.validate_done_output.return_value = "exit"

        # _record_think_results returns the expected structure
        from dana.core.agent.base_star_agent import EXIT_STAR_LOOP_FLAG

        expected_trace = {"trace_thoughts": {"response": "Hi!", "tool_calls": [], EXIT_STAR_LOOP_FLAG: True}}
        mock_runtime_patch = patch.object(agent, "_runtime", mock_runtime)
        record_patch = patch.object(agent, "_record_think_results", return_value=expected_trace)
        compress_patch = patch.object(agent, "_maybe_compress_timeline_async", new=AsyncMock())

        result_holder: dict = {}
        trace_percepts = {"timeline": agent._timeline}

        with mock_runtime_patch, record_patch, compress_patch:
            delta_events = []
            async for event in agent._think_stream(trace_percepts, result_holder):
                delta_events.append(event)

        # Should have yielded TEXT_DELTA for each chunk
        assert all(e.event_type == StreamEventType.TEXT_DELTA for e in delta_events)
        assert [e.data for e in delta_events] == ["<done>true</done>", "<response>Hi!</response>"]

        # result_holder should be populated
        assert "trace_thoughts" in result_holder
        assert result_holder["trace_thoughts"] == expected_trace

    @pytest.mark.asyncio
    async def test_exits_early_on_exit_star_loop_flag(self):
        """If trace_percepts has EXIT flag set, _think_stream yields nothing."""
        agent = _make_agent()
        from dana.core.agent.base_star_agent import EXIT_STAR_LOOP_FLAG

        trace_percepts = {EXIT_STAR_LOOP_FLAG: True}
        result_holder: dict = {}

        events = []
        async for event in agent._think_stream(trace_percepts, result_holder):
            events.append(event)

        assert events == []
        assert "trace_thoughts" in result_holder
