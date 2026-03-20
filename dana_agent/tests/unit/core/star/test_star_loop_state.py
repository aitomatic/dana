"""
Tests for Timeline.count_iterations() and STARAgent.resume_from_timeline().

count_iterations() replaces the deleted STARLoopState class — it counts STAR loop
iterations (AGENT_RESPONSE or TOOL_CALL entries) from the persistent timeline.
"""

from dana.core.timeline.timeline import Timeline, TimelineEntry, TimelineEntryType


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
    """Ephemeral CONTEXT entry (excluded from iteration counting)."""
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
        assert tl.count_iterations() == 0

    def test_user_message_only_yields_zero_iterations(self):
        tl = _make_timeline(_user("hello"))
        assert tl.count_iterations() == 0


# ---------------------------------------------------------------------------
# Single-iteration (agent responds, no tools)
# ---------------------------------------------------------------------------


class TestSingleResponseIteration:
    def test_one_response_is_one_iteration(self):
        tl = _make_timeline(
            _user("What's 2+2?"),
            _response("4"),
        )
        assert tl.count_iterations() == 1

    def test_agent_response_counts_as_iteration(self):
        tl = _make_timeline(_user("hi"), _response("hello"))
        assert tl.count_iterations() == 1


# ---------------------------------------------------------------------------
# Tool-call round
# ---------------------------------------------------------------------------


class TestToolCallIteration:
    def test_tool_call_counts_as_one_iteration(self):
        tl = _make_timeline(
            _user("Search python"),
            _tool_call(tool_calls=[{"function": "search:web", "arguments": {"query": "python"}}]),
        )
        assert tl.count_iterations() == 1

    def test_agent_thoughts_before_tool_call_not_extra_iteration(self):
        """AGENT_THOUGHTS must NOT add an extra iteration."""
        tl = _make_timeline(
            _user("Search and report"),
            _thought("Let me search first"),
            _tool_call(tool_calls=[{"function": "search:web", "arguments": {}}]),
        )
        # Only one TOOL_CALL → one iteration
        assert tl.count_iterations() == 1

    def test_resource_result_does_not_add_iteration(self):
        tl = _make_timeline(
            _user("Search python"),
            _tool_call(tool_calls=[{"function": "search:web", "arguments": {}}]),
            _resource_result("some search results", tool_call_id="call-1"),
        )
        assert tl.count_iterations() == 1


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
        assert tl.count_iterations() == 2

    def test_two_tool_rounds_then_response_is_three_iterations(self):
        tl = _make_timeline(
            _user("Do A then B then answer"),
            _tool_call(tool_calls=[{"function": "tool_a", "arguments": {}}]),
            _resource_result("a-result"),
            _tool_call(tool_calls=[{"function": "tool_b", "arguments": {}}]),
            _resource_result("b-result"),
            _response("Done."),
        )
        assert tl.count_iterations() == 3


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
        # CONTEXT is ephemeral → excluded → only 1 think round
        assert tl.count_iterations() == 1


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


# ---------------------------------------------------------------------------
# resume_session (high-level)
# ---------------------------------------------------------------------------


class TestResumeSession:
    """Tests for STARAgent.resume_session() — loads from disk via read_since."""

    def test_resume_session_sets_session_id(self):
        agent = _make_agent()
        entries = [_user("hi"), _response("hello")]
        agent._timeline.read_since = lambda checkpoint: iter(entries)

        agent.resume_session("saved-session-42")

        assert agent._session_id == "saved-session-42"

    def test_resume_session_loads_timeline_entries(self):
        agent = _make_agent()
        entries = [_user("hi"), _response("hello")]
        agent._timeline.read_since = lambda checkpoint: iter(entries)

        agent.resume_session("sess-1")

        assert len(agent._timeline.timeline) == 2
        assert agent._timeline.timeline[0].content == "hi"

    def test_resume_session_syncs_star_loop_count(self):
        agent = _make_agent()
        entries = [
            _user("search"),
            _tool_call(tool_calls=[{"function": "search:web", "arguments": {}}]),
            _resource_result("results"),
            _response("Done."),
        ]
        agent._timeline.read_since = lambda checkpoint: iter(entries)

        agent.resume_session("sess-2")

        # 1 TOOL_CALL + 1 AGENT_RESPONSE = 2 iterations
        assert agent._star_loop_count == 2

    def test_resume_session_empty_history(self):
        agent = _make_agent()
        agent._star_loop_count = 5
        agent._timeline.read_since = lambda checkpoint: iter([])

        agent.resume_session("empty-sess")

        assert agent._star_loop_count == 0
        assert agent._session_id == "empty-sess"
        assert len(agent._timeline.timeline) == 0

    def test_resume_session_sets_id_before_read_since(self):
        """_session_id must be set before read_since (which may depend on it)."""
        agent = _make_agent()
        call_order: list[str] = []

        def tracking_read_since(checkpoint):
            call_order.append(f"read_since:session={agent._session_id}")
            return iter([_user("hi"), _response("hello")])

        agent._timeline.read_since = tracking_read_since

        agent.resume_session("order-test-session")

        assert len(call_order) == 1
        assert "order-test-session" in call_order[0]
