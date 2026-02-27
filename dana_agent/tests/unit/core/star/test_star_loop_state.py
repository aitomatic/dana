"""
Tests for STARLoopState — derivable STAR loop state from a Timeline.
"""

from dana.core.agent.star_loop_state import STARLoopState
from dana.core.agent.timeline import Timeline, TimelineEntry, TimelineEntryType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_timeline(*entries: TimelineEntry) -> Timeline:
    """Build a Timeline with the given entries (no agent / repository)."""
    tl = Timeline()
    for entry in entries:
        tl.add_entry(entry)
    return tl


def _user(content: str) -> TimelineEntry:
    return TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content=content)


def _response(content: str) -> TimelineEntry:
    return TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content=content)


def _thought(content: str) -> TimelineEntry:
    return TimelineEntry(entry_type=TimelineEntryType.AGENT_THOUGHTS, content=content)


def _tool_call(content: str = "", tool_calls: list | None = None) -> TimelineEntry:
    return TimelineEntry(
        entry_type=TimelineEntryType.TOOL_CALL,
        content=content,
        tool_calls=tool_calls,
    )


def _resource_result(content: str, tool_call_id: str | None = None) -> TimelineEntry:
    return TimelineEntry(
        entry_type=TimelineEntryType.RESOURCE_RESULT,
        content=content,
        tool_call_id=tool_call_id,
    )


def _context_entry(content: str = "date: today") -> TimelineEntry:
    """Ephemeral CONTEXT entry (excluded from state derivation)."""
    return TimelineEntry(
        entry_type=TimelineEntryType.CONTEXT,
        content=content,
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# Empty / minimal timelines
# ---------------------------------------------------------------------------


class TestEmptyTimeline:
    def test_empty_timeline_yields_zero_iterations(self):
        tl = _make_timeline()
        state = STARLoopState.from_timeline(tl)

        assert state.iteration == 0
        assert state.last_response is None
        assert state.last_tool_calls == []
        assert state.last_tool_results == []
        assert state.is_done is False

    def test_user_message_only_yields_zero_iterations(self):
        tl = _make_timeline(_user("hello"))
        state = STARLoopState.from_timeline(tl)

        assert state.iteration == 0
        assert state.is_done is False


# ---------------------------------------------------------------------------
# Single-iteration (agent responds, no tools)
# ---------------------------------------------------------------------------


class TestSingleResponseIteration:
    def test_one_response_is_one_iteration(self):
        tl = _make_timeline(
            _user("What's 2+2?"),
            _response("4"),
        )
        state = STARLoopState.from_timeline(tl)

        assert state.iteration == 1
        assert state.last_response == "4"
        assert state.last_tool_calls == []
        assert state.last_tool_results == []
        assert state.is_done is True

    def test_is_done_true_after_agent_response(self):
        tl = _make_timeline(_user("hi"), _response("hello"))
        state = STARLoopState.from_timeline(tl)
        assert state.is_done is True


# ---------------------------------------------------------------------------
# Tool-call round (agent calls a tool, not yet done)
# ---------------------------------------------------------------------------


class TestToolCallIteration:
    def test_tool_call_counts_as_one_iteration(self):
        tool_calls = [{"function": "search:web", "arguments": {"query": "python"}}]
        tl = _make_timeline(
            _user("Search python"),
            _tool_call(tool_calls=tool_calls),
        )
        state = STARLoopState.from_timeline(tl)

        assert state.iteration == 1
        assert state.is_done is False
        assert state.last_tool_calls == tool_calls

    def test_tool_results_captured_after_tool_call(self):
        tl = _make_timeline(
            _user("Search python"),
            _tool_call(tool_calls=[{"function": "search:web", "arguments": {}}]),
            _resource_result("some search results", tool_call_id="call-1"),
        )
        state = STARLoopState.from_timeline(tl)

        assert len(state.last_tool_results) == 1
        assert state.last_tool_results[0]["content"] == "some search results"
        assert state.last_tool_results[0]["tool_call_id"] == "call-1"

    def test_legacy_xml_tool_call_stored_in_content(self):
        xml = '<function_call><invoke name="search:web"><parameter name="query">foo</parameter></invoke></function_call>'
        tl = _make_timeline(
            _user("do something"),
            _tool_call(content=xml),  # no tool_calls field — legacy XML
        )
        state = STARLoopState.from_timeline(tl)

        assert state.iteration == 1
        assert len(state.last_tool_calls) == 1
        assert state.last_tool_calls[0]["content"] == xml

    def test_agent_thoughts_before_tool_call_not_extra_iteration(self):
        """AGENT_THOUGHTS emitted alongside tool calls must NOT add an extra iteration."""
        tl = _make_timeline(
            _user("Search and report"),
            _thought("Let me search first"),
            _tool_call(tool_calls=[{"function": "search:web", "arguments": {}}]),
        )
        state = STARLoopState.from_timeline(tl)

        # Only one TOOL_CALL → one iteration
        assert state.iteration == 1


# ---------------------------------------------------------------------------
# Multi-round (tool call → result → response)
# ---------------------------------------------------------------------------


class TestMultiRoundIterations:
    def test_tool_call_then_response_is_two_iterations(self):
        tl = _make_timeline(
            _user("Search and summarize"),
            _tool_call(tool_calls=[{"function": "search:web", "arguments": {}}]),
            _resource_result("results"),
            _response("Here is the summary."),
        )
        state = STARLoopState.from_timeline(tl)

        assert state.iteration == 2
        assert state.is_done is True
        assert state.last_response == "Here is the summary."
        assert state.last_tool_calls == []  # cleared when AGENT_RESPONSE appears
        assert state.last_tool_results == []

    def test_two_tool_rounds_then_response_is_three_iterations(self):
        tl = _make_timeline(
            _user("Do A then B then answer"),
            _tool_call(tool_calls=[{"function": "tool_a", "arguments": {}}]),
            _resource_result("a-result"),
            _tool_call(tool_calls=[{"function": "tool_b", "arguments": {}}]),
            _resource_result("b-result"),
            _response("Done."),
        )
        state = STARLoopState.from_timeline(tl)

        assert state.iteration == 3
        assert state.is_done is True

    def test_last_tool_results_reflect_most_recent_round_only(self):
        """After a second tool call, last_tool_results should only include the second round."""
        tl = _make_timeline(
            _user("multi-step"),
            _tool_call(tool_calls=[{"function": "step1", "arguments": {}}]),
            _resource_result("step1-result"),
            _tool_call(tool_calls=[{"function": "step2", "arguments": {}}]),
            _resource_result("step2-result"),
        )
        state = STARLoopState.from_timeline(tl)

        assert len(state.last_tool_results) == 1
        assert state.last_tool_results[0]["content"] == "step2-result"


# ---------------------------------------------------------------------------
# Ephemeral entries are ignored
# ---------------------------------------------------------------------------


class TestEphemeralEntriesIgnored:
    def test_context_entry_not_counted(self):
        tl = _make_timeline(
            _context_entry("Current date: 2025-01-01"),
            _user("hello"),
            _response("hi"),
        )
        state = STARLoopState.from_timeline(tl)

        # CONTEXT is ephemeral → excluded → only 1 think round
        assert state.iteration == 1


# ---------------------------------------------------------------------------
# from_timeline_at_entry (replay / debug)
# ---------------------------------------------------------------------------


class TestFromTimelineAtEntry:
    def _build_multi_entry_timeline(self) -> Timeline:
        """
        Timeline:
          [0] USER_MESSAGE    "Do A then answer"
          [1] TOOL_CALL       tool_a
          [2] RESOURCE_RESULT a-result
          [3] AGENT_RESPONSE  "Done."
        """
        return _make_timeline(
            _user("Do A then answer"),
            _tool_call(tool_calls=[{"function": "tool_a", "arguments": {}}]),
            _resource_result("a-result"),
            _response("Done."),
        )

    def test_at_entry_0_is_empty_state(self):
        tl = self._build_multi_entry_timeline()
        state = STARLoopState.from_timeline_at_entry(tl, 0)

        assert state.iteration == 0
        assert state.is_done is False

    def test_at_entry_2_sees_tool_call_not_result(self):
        """After entry index 2 (exclusive), we've seen entries[0:2] = USER + TOOL_CALL."""
        tl = self._build_multi_entry_timeline()
        state = STARLoopState.from_timeline_at_entry(tl, 2)

        assert state.iteration == 1
        assert state.is_done is False
        assert len(state.last_tool_calls) == 1

    def test_at_entry_3_sees_tool_call_and_result(self):
        """entries[0:3] = USER + TOOL_CALL + RESOURCE_RESULT."""
        tl = self._build_multi_entry_timeline()
        state = STARLoopState.from_timeline_at_entry(tl, 3)

        assert state.iteration == 1
        assert state.is_done is False
        assert len(state.last_tool_results) == 1

    def test_at_entry_4_full_state(self):
        tl = self._build_multi_entry_timeline()
        full = STARLoopState.from_timeline(tl)
        at_end = STARLoopState.from_timeline_at_entry(tl, 4)

        assert at_end.iteration == full.iteration
        assert at_end.is_done == full.is_done
        assert at_end.last_response == full.last_response

    def test_negative_index_slices_from_end(self):
        """entry_index=-1 means entries[:-1] (exclude the last entry)."""
        tl = self._build_multi_entry_timeline()
        # entries[:-1] = USER + TOOL_CALL + RESOURCE_RESULT
        state = STARLoopState.from_timeline_at_entry(tl, -1)

        assert state.iteration == 1
        assert state.is_done is False

    def test_out_of_bounds_index_clamps_to_full(self):
        tl = self._build_multi_entry_timeline()
        full = STARLoopState.from_timeline(tl)
        clamped = STARLoopState.from_timeline_at_entry(tl, 9999)

        assert clamped.iteration == full.iteration

    def test_from_timeline_equals_at_entry_with_full_count(self):
        """from_timeline and from_timeline_at_entry(len) should yield same result."""
        tl = self._build_multi_entry_timeline()
        full = STARLoopState.from_timeline(tl)
        at_len = STARLoopState.from_timeline_at_entry(tl, len(tl.timeline))

        assert full.iteration == at_len.iteration
        assert full.is_done == at_len.is_done
        assert full.last_response == at_len.last_response


# ---------------------------------------------------------------------------
# resume_from_timeline on STARAgent
# ---------------------------------------------------------------------------


def _make_agent():
    """Create a minimal STARAgent without LLM calls or registry side-effects."""
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


class TestResumeFromTimeline:
    """Integration tests for STARAgent.resume_from_timeline()."""

    def test_resume_sets_timeline(self):
        agent = _make_agent()
        tl = _make_timeline(_user("hi"), _response("hello"))
        agent.resume_from_timeline(tl)

        assert agent._timeline is tl

    def test_resume_derives_star_loop_count(self):
        agent = _make_agent()
        tl = _make_timeline(
            _user("search"),
            _tool_call(tool_calls=[{"function": "search:web", "arguments": {}}]),
            _resource_result("results"),
            _response("Here you go."),
        )
        agent.resume_from_timeline(tl)

        # 1 TOOL_CALL + 1 AGENT_RESPONSE = iteration 2
        assert agent._star_loop_count == 2

    def test_resume_sets_session_id_when_provided(self):
        agent = _make_agent()
        tl = Timeline()
        agent.resume_from_timeline(tl, session_id="new-session-123")

        assert agent._session_id == "new-session-123"

    def test_resume_keeps_original_session_id_when_not_provided(self):
        agent = _make_agent()
        original_id = agent._session_id
        tl = Timeline()
        agent.resume_from_timeline(tl)

        assert agent._session_id == original_id

    def test_resume_empty_timeline_resets_count(self):
        agent = _make_agent()
        agent._star_loop_count = 5  # simulate previous loops
        agent.resume_from_timeline(Timeline())

        assert agent._star_loop_count == 0
