"""
Regression test: tool execution errors must preserve tool_call_id in timeline.

Reproduces the bug from a real session where:
1. LLM calls Grep with unsupported kwargs (e.g. "-i": true instead of "case_insensitive": true)
2. SearchResource.grep() raises TypeError for the unknown kwarg
3. _act_async stores the error as UNKNOWN_TOOL_CALL (because _create_tool_error returns
   type="execution_error", not type="resource")
4. CompressedTimeline._timeline_entry_to_native_message maps UNKNOWN_TOOL_CALL to
   role="assistant" instead of role="tool", dropping the tool_call_id
5. The next LLM call fails: "tool_call_ids did not have response messages"

Timeline source: tests/regression/fixtures/timeline-with-errors.json
"""

import asyncio
import json
from pathlib import Path

import pytest

from dana.core.agent.builtin_agents.dana_coding_agent import DanaCodingAgent
from dana.core.timeline.compressed_timeline import CompressedTimeline
from dana.core.timeline.timeline import TimelineEntry, TimelineEntryType


TIMELINE_PATH = Path(__file__).resolve().parent / "fixtures" / "timeline-with-errors.json"


def _load_timeline_data() -> dict:
    """Load the error timeline JSON."""
    if not TIMELINE_PATH.exists():
        pytest.skip(f"Timeline fixture not found: {TIMELINE_PATH}")
    with open(TIMELINE_PATH) as f:
        return json.load(f)


def _find_tool_calls_with_bad_kwargs(timeline_data: dict) -> list[dict]:
    """Find tool_call entries from the timeline that contain unsupported kwargs.

    These are entries where the LLM sent arguments like "-i", "-n", "-C"
    which are not valid Python parameter names for SearchResource.grep().
    """
    bad_tool_call_entries = []
    for entry in timeline_data["entries"]:
        if entry.get("type") != "tool_call":
            continue
        for tc in entry.get("tool_calls", []):
            args = tc.get("arguments", {})
            # Check for ripgrep-style flag arguments that aren't valid Python kwargs
            has_bad_kwargs = any(k.startswith("-") for k in args)
            if has_bad_kwargs:
                bad_tool_call_entries.append(entry)
                break
    return bad_tool_call_entries


def _extract_tool_calls_from_entry(entry: dict) -> list[dict]:
    """Extract tool_calls list from a timeline entry in the format _act_async expects."""
    return entry.get("tool_calls", [])


class TestToolCallErrorTimeline:
    """Test that tool execution errors are correctly represented in the timeline."""

    def test_timeline_has_error_entries(self):
        """Verify the timeline fixture contains the expected error-producing tool calls."""
        data = _load_timeline_data()
        bad_entries = _find_tool_calls_with_bad_kwargs(data)
        assert len(bad_entries) > 0, "Expected at least one tool_call entry with unsupported kwargs"

        # Verify we can find the specific bad kwarg patterns
        all_bad_args = set()
        for entry in bad_entries:
            for tc in entry.get("tool_calls", []):
                for k in tc.get("arguments", {}):
                    if k.startswith("-"):
                        all_bad_args.add(k)
        assert (
            "-i" in all_bad_args or "-n" in all_bad_args or "-C" in all_bad_args
        ), f"Expected ripgrep-style flags in bad kwargs, got: {all_bad_args}"

    def test_act_async_preserves_tool_call_id_on_error(self):
        """When a tool call fails, _act_async must store the error with the correct tool_call_id.

        This is the core regression: the error result must be stored as a timeline entry
        that converts to role="tool" (not role="assistant") so the LLM API accepts it.
        """
        data = _load_timeline_data()
        bad_entries = _find_tool_calls_with_bad_kwargs(data)
        assert bad_entries, "No bad tool call entries found in timeline"

        # Use the first entry that has a mix of good and bad tool calls
        tool_calls = _extract_tool_calls_from_entry(bad_entries[0])

        # Create the agent with a dummy cwd (we don't need real files for this test)
        agent = DanaCodingAgent(
            agent_id="test-error-timeline",
            agent_type="dana_coding_agent",
            llm_provider="anthropic_like",
            model="kimi-k2-thinking-turbo",
            cwd="/tmp",
        )

        # First, simulate what _think_async does: add the tool_call entry to the timeline
        agent._timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.TOOL_CALL,
                content="",
                tool_calls=tool_calls,
            )
        )

        timeline_len_before = len(agent._timeline.timeline)

        # Build trace_thoughts as _think_async would produce
        trace_thoughts = {
            "response": "Let me search for connectivity information...",
            "tool_calls": tool_calls,
            "done": False,
        }

        # Run _act_async — this will execute the tool calls, some will fail
        _ = asyncio.run(agent._act_async(trace_thoughts))

        # Verify tool results were added to timeline
        new_entries = agent._timeline.timeline[timeline_len_before:]
        assert len(new_entries) == len(tool_calls), f"Expected {len(tool_calls)} result entries, got {len(new_entries)}"

        # Find the entries for tool calls that had bad kwargs
        bad_tc_ids = set()
        for tc in tool_calls:
            args = tc.get("arguments", {})
            if any(k.startswith("-") for k in args):
                bad_tc_ids.add(tc.get("tool_call_id"))

        for entry in new_entries:
            if entry.tool_call_id in bad_tc_ids:
                # THIS IS THE BUG: error results get entry_type=UNKNOWN_TOOL_CALL
                # which maps to role="assistant" instead of role="tool"
                assert entry.tool_call_id is not None, "Error result entry must have tool_call_id preserved"
                # The entry type should allow conversion to role="tool"
                # Currently it's UNKNOWN_TOOL_CALL which converts to role="assistant" (BUG)
                assert entry.entry_type in (
                    TimelineEntryType.RESOURCE_RESULT,
                    TimelineEntryType.WORKFLOW_RESULT,
                    TimelineEntryType.UNKNOWN_TOOL_CALL,  # current behavior
                ), f"Unexpected entry type for error result: {entry.entry_type}"

    def test_unknown_tool_call_native_message_role(self):
        """UNKNOWN_TOOL_CALL entries with tool_call_id must convert to role='tool', not 'assistant'.

        This tests the CompressedTimeline._timeline_entry_to_native_message conversion.
        When a tool execution error has a tool_call_id, the native message must use
        role="tool" so the LLM API can match it to the corresponding tool_call.
        """
        data = _load_timeline_data()

        # Find the error entry in the timeline (type=unknown_tool_call)
        error_entries = [e for e in data["entries"] if e.get("type") == "unknown_tool_call" and e.get("tool_call_id")]
        assert error_entries, "No unknown_tool_call entries with tool_call_id found in timeline"

        error_entry = error_entries[0]
        timeline_entry = TimelineEntry.from_dict(error_entry)

        # Verify the entry has tool_call_id
        assert timeline_entry.tool_call_id is not None
        assert timeline_entry.entry_type == TimelineEntryType.UNKNOWN_TOOL_CALL

        # Create a CompressedTimeline and test the conversion
        agent = DanaCodingAgent(
            agent_id="test-native-msg",
            agent_type="dana_coding_agent",
            llm_provider="anthropic_like",
            model="kimi-k2-thinking-turbo",
            cwd="/tmp",
        )
        compressed_timeline: CompressedTimeline = agent._timeline

        # Convert the error entry to a native message
        native_msg = compressed_timeline._timeline_entry_to_native_message(timeline_entry)

        # THIS IS THE ASSERTION THAT CURRENTLY FAILS:
        # UNKNOWN_TOOL_CALL with a tool_call_id should be role="tool", not "assistant"
        assert native_msg.role == "tool", (
            f"Expected role='tool' for UNKNOWN_TOOL_CALL with tool_call_id={timeline_entry.tool_call_id}, "
            f"got role='{native_msg.role}'. "
            "Error results must use role='tool' so the LLM API can match them to their tool_calls."
        )
        assert (
            native_msg.tool_call_id == timeline_entry.tool_call_id
        ), "Native message must preserve the tool_call_id from the timeline entry"

    def test_bad_kwargs_error_feeds_back_to_timeline(self):
        """When a tool call has unsupported kwargs, the error must be captured in the timeline
        with the correct tool_call_id so the LLM can see the error and self-correct.

        The system should NOT silently strip unknown kwargs — the LLM needs to learn
        from the error. What matters is that the error doesn't break the agent loop.
        """
        data = _load_timeline_data()
        bad_entries = _find_tool_calls_with_bad_kwargs(data)
        assert bad_entries, "No bad tool call entries found in timeline"

        tool_calls = _extract_tool_calls_from_entry(bad_entries[0])

        agent = DanaCodingAgent(
            agent_id="test-error-feedback",
            agent_type="dana_coding_agent",
            llm_provider="anthropic_like",
            model="kimi-k2-thinking-turbo",
            cwd="/tmp",
        )

        # Simulate _think_async adding the tool_call entry
        agent._timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.TOOL_CALL,
                content="",
                tool_calls=tool_calls,
            )
        )

        trace_thoughts = {
            "response": "Let me search...",
            "tool_calls": tool_calls,
            "done": False,
        }

        # Run _act_async — bad kwargs will cause TypeError, which should be caught
        _ = asyncio.run(agent._act_async(trace_thoughts))

        # Find entries for tool calls that had bad kwargs
        bad_tc_ids = set()
        for tc in tool_calls:
            args = tc.get("arguments", {})
            if any(k.startswith("-") for k in args):
                bad_tc_ids.add(tc.get("tool_call_id"))

        # Verify error entries have tool_call_id AND convert to role="tool"
        compressed_timeline: CompressedTimeline = agent._timeline
        for entry in agent._timeline.timeline:
            if entry.tool_call_id in bad_tc_ids:
                assert entry.tool_call_id is not None, "Error entry must preserve tool_call_id"

                # The entry must convert to role="tool" so the LLM API accepts it
                native_msg = compressed_timeline._timeline_entry_to_native_message(entry)
                assert native_msg.role == "tool", (
                    f"Error entry with tool_call_id={entry.tool_call_id} converted to "
                    f"role='{native_msg.role}' — must be 'tool' so the LLM API can match it "
                    "to the corresponding tool_call."
                )
                assert native_msg.tool_call_id == entry.tool_call_id

    def test_full_round_trip_timeline_to_native_messages(self):
        """Full round-trip: load timeline with errors, convert to native messages,
        verify all tool_call_ids have matching tool results.

        This reproduces the exact LLM API error:
        "tool_call_ids did not have response messages: <id>"
        """
        data = _load_timeline_data()

        agent = DanaCodingAgent(
            agent_id="test-roundtrip",
            agent_type="dana_coding_agent",
            llm_provider="anthropic_like",
            model="kimi-k2-thinking-turbo",
            cwd="/tmp",
        )

        # Load entries only (without pre-saved native_messages) to force reconversion
        # through _timeline_entry_to_native_message, which is where the bug was.
        # The saved native_messages in the JSON were generated with the buggy code
        # and already have Grep_16 as role="assistant".
        agent._timeline.load_from_entries(
            entries=data["entries"],
        )

        compressed_timeline: CompressedTimeline = agent._timeline
        native_messages = compressed_timeline._native_messages

        # Collect all tool_call_ids from assistant messages (tool_calls)
        expected_tool_ids: set[str] = set()
        for msg in native_messages:
            if msg.role == "assistant" and msg.tool_calls:
                for tc in msg.tool_calls:
                    if tc.id:
                        expected_tool_ids.add(tc.id)

        # Collect all tool_call_ids from tool result messages
        responded_tool_ids: set[str] = set()
        for msg in native_messages:
            if msg.role == "tool" and msg.tool_call_id:
                responded_tool_ids.add(msg.tool_call_id)

        # Every tool_call_id from assistant must have a matching tool result
        missing_ids = expected_tool_ids - responded_tool_ids
        assert not missing_ids, (
            f"Tool call IDs without matching tool result messages: {missing_ids}. "
            "This would cause the LLM API to reject the request with: "
            "'tool_call_ids did not have response messages'. "
            "Likely cause: UNKNOWN_TOOL_CALL entries are being converted to role='assistant' "
            "instead of role='tool'."
        )
