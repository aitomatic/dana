"""
STARAgentStreamingMixin — streaming extensions for STARAgent.

Provides aquery_stream(), _run_aquery_stream(), and _think_stream().
Mixed into STARAgent so all methods retain self access.
"""

from collections.abc import AsyncIterator

import structlog

from dana.common.protocols import DictParams
from dana.common.protocols.types import LearningPhase

from ..runtime.protocols import StreamEvent, StreamEventType
from ..timeline.timeline import Timeline


logger = structlog.get_logger()


class STARAgentStreamingMixin:
    """Mixin that adds streaming query support to STARAgent.

    Depends on the following attributes / methods being available on self:
        - _star_loop_count, _session_id, _event_log, _timeline
        - _runtime, llm_client, object_id, agent_type, agent_id
        - set_session_id(), _do_exit_star_loop(), _mark_star_loop_exit()
        - _see(), _act_async(), _reflect()
        - _maybe_compress_timeline_async(), _record_think_results()
        - MAX_ITERATIONS
    """

    async def _think_stream(
        self,
        trace_percepts: DictParams,
        result_holder: dict,
    ) -> AsyncIterator[StreamEvent]:
        """Streaming think phase. Yields StreamEvents while the LLM responds.

        Handles typed LLMStreamChunk objects: text_delta, tool_use, thinking.
        Builds a synthetic LLMResponse with both text and tool_calls so
        parse_response works for native tool calling agents.

        Args:
            trace_percepts: Percepts from the SEE phase (timeline must be present).
            result_holder:  Mutable dict; populated with {"trace_thoughts": ...}
                            after streaming completes.

        Yields:
            StreamEvent: TEXT_DELTA, TOOL_CALL_START, THINKING events.
        """
        import json

        from dana.common.llm.types import LLMResponse

        trace_percepts = trace_percepts or {}
        if self._do_exit_star_loop(trace_percepts) or not trace_percepts:
            result_holder["trace_thoughts"] = {"trace_thoughts": self._mark_star_loop_exit(trace_percepts)}
            return

        iteration = self._star_loop_count
        timeline: Timeline = trace_percepts.get("timeline", self._timeline)
        trace_percepts.pop("timeline", None)

        await self._maybe_compress_timeline_async(timeline)
        llm_messages = self._runtime.build_prompt(self, timeline)

        # Resolve stream source
        if hasattr(self._runtime, "_llm_caller"):
            stream_src = self._runtime._llm_caller.call_llm_stream(llm_messages)
        else:
            stream_src = self.llm_client.stream(
                llm_messages,
                agent_id=self.object_id,
                agent_type=self.agent_type,
            )

        # Collect chunks by type.
        # Text is emitted as THINKING during streaming because we can't know
        # if tool_calls will follow.  After the stream ends we reclassify:
        #   tool_calls present  → text was thinking (already emitted correctly)
        #   no tool_calls       → text is response, emit a single TEXT_DELTA
        text_chunks: list[str] = []
        tool_calls_from_stream: list[dict] = []
        thinking_chunks: list[str] = []

        async for chunk in stream_src:
            if chunk.type == "text_delta":
                text_chunks.append(chunk.content)
                # Emit as THINKING; reclassified after stream completes
                yield StreamEvent(event_type=StreamEventType.THINKING, data=chunk.content, iteration=iteration)
            elif chunk.type == "tool_use":
                tool_calls_from_stream.append(chunk.tool_call)
                yield StreamEvent(event_type=StreamEventType.TOOL_CALL_START, data=[chunk.tool_call], iteration=iteration)
            elif chunk.type == "thinking":
                thinking_chunks.append(chunk.content)
                yield StreamEvent(event_type=StreamEventType.THINKING, data=chunk.content, iteration=iteration)

        buffered_text = "".join(text_chunks)

        # Reclassify: if no tool calls, the text is the actual response
        if not tool_calls_from_stream and buffered_text:
            yield StreamEvent(event_type=StreamEventType.TEXT_DELTA, data=buffered_text, iteration=iteration)

        # Build synthetic LLMResponse with BOTH text and tool calls
        synthetic_response = LLMResponse(
            content=buffered_text,
            model="streamed",
            finish_reason="stop" if not tool_calls_from_stream else "tool_use",
            tool_calls=[
                type(
                    "ToolCall",
                    (),
                    {
                        "id": tc["id"],
                        "function": type(
                            "Function",
                            (),
                            {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["input"]) if isinstance(tc["input"], dict) else tc["input"],
                            },
                        )(),
                    },
                )()
                for tc in tool_calls_from_stream
            ]
            if tool_calls_from_stream
            else None,
            reasoning_content="".join(thinking_chunks) if thinking_chunks else None,
        )

        parsed = self._runtime.parse_response(synthetic_response)
        response, reasoning, tool_calls, done, todo_list = (
            parsed.response,
            parsed.reasoning,
            parsed.tool_calls,
            parsed.done,
            parsed.todo_list,
        )

        has_tool_calls = bool(tool_calls)
        has_response = bool(response and response.strip())
        output_state = self._runtime.validate_done_output(done, has_tool_calls, has_response)

        # No retry loop for streaming (YAGNI — keep simple)
        if output_state == "retry":
            output_state = "exit"

        trace_result = self._record_think_results(
            timeline,
            trace_percepts,
            response,
            reasoning,
            tool_calls,
            done,
            todo_list,
            output_state,
        )
        result_holder["trace_thoughts"] = trace_result

    async def aquery_stream(self, **kwargs) -> AsyncIterator[StreamEvent]:
        """Streaming version of aquery with session management.

        Yields StreamEvent objects: TEXT_DELTA during LLM generation,
        TOOL_CALL_START and TOOL_RESULT during tool execution, then DONE.

        Args:
            **kwargs: Same kwargs as aquery() (message, caller_message, etc.)

        Yields:
            StreamEvent: Stream events throughout the STAR loop.
        """
        # Session management (mirrors aquery())
        new_session_id = kwargs.get("session_id")
        if new_session_id is not None:
            self.set_session_id(new_session_id)
        session_id = self._session_id

        self._star_loop_count = 0

        if hasattr(self, "_event_log") and self._event_log is not None:
            self._event_log._current_session_id = session_id

        try:
            async for event in self._run_aquery_stream(kwargs):
                yield event
        finally:
            if hasattr(self, "_event_log") and self._event_log is not None:
                self._event_log.save(session_id)
            if hasattr(self, "_timeline") and self._timeline is not None:
                self._timeline.save(session_id)

    async def _run_aquery_stream(self, kwargs: DictParams) -> AsyncIterator[StreamEvent]:
        """Inner streaming STAR loop (no session management).

        Yields StreamEvent objects from the STAR loop iterations.
        """
        import asyncio

        trace_inputs: DictParams = {"trace_inputs": kwargs}
        trace_outputs: DictParams = {}

        for _ in range(self.MAX_ITERATIONS):
            try:
                # SEE phase (sync — no streaming needed)
                trace_percepts = self._see(trace_inputs.get("trace_inputs", {}))

                # THINK phase — stream text deltas
                result_holder: dict = {}
                async for event in self._think_stream(
                    trace_percepts.get("trace_percepts", {}),
                    result_holder,
                ):
                    yield event

                # result_holder now contains {"trace_thoughts": ...}
                trace_thoughts_wrapper = result_holder.get("trace_thoughts", {"trace_thoughts": {}})
                trace_thoughts_inner = trace_thoughts_wrapper.get("trace_thoughts", {})
                iteration = self._star_loop_count

                # TOOL_CALL_START already emitted by _think_stream() — no duplicate here

                # ACT phase (async — uses existing _act_async)
                trace_outputs = await self._act_async(trace_thoughts_inner)
                tool_results = trace_outputs.get("trace_outputs", {}).get("tool_results", [])

                # Yield TOOL_RESULT events after execution
                if tool_results:
                    yield StreamEvent(
                        event_type=StreamEventType.TOOL_RESULT,
                        data=tool_results,
                        iteration=iteration,
                    )

                # Trigger acquisitive learning asynchronously
                if not self._do_exit_star_loop(trace_outputs.get("trace_outputs", {})):
                    acquisitive_input = trace_outputs.get("trace_outputs", {}).copy()
                    acquisitive_input["phase"] = LearningPhase.ACQUISITIVE

                    async def _async_reflect(acq_input):
                        try:
                            self._reflect(acq_input)
                        except Exception as reflect_err:
                            logger.error("Async reflection failed", error=str(reflect_err))

                    asyncio.create_task(_async_reflect(acquisitive_input))

                if self._do_exit_star_loop(trace_outputs.get("trace_outputs", {})):
                    break

                # Prepare next iteration inputs from tool results
                trace_inputs = {"trace_inputs": trace_outputs.get("trace_outputs", {})}

            except Exception as exc:
                logger.error("Error in aquery_stream", error=str(exc))
                yield StreamEvent(
                    event_type=StreamEventType.ERROR,
                    data=str(exc),
                    iteration=self._star_loop_count,
                )
                return

        yield StreamEvent(event_type=StreamEventType.DONE, data=None, iteration=self._star_loop_count)
