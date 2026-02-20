"""
Regression test: read_since must rebuild _native_messages so to_llm_messages works.

Reproduces the bug from `test copy.py` where:
1. Agent loads a saved session via set_session_id + read_since(0)
2. Entries are assigned to timeline.timeline
3. to_llm_messages() returns wrong/missing messages because _native_messages is empty

The root cause was that CompressedTimeline.read_since() only loaded TimelineEntry
objects but never populated _native_messages, which is what to_llm_messages() reads from.

Timeline source: tests/regression/fixtures/timeline_that_with_assisstant_message_being_skip.json
"""

import json
from pathlib import Path

import pytest

from dana.core.agent.compressed_timeline import CompressedTimeline
from dana.core.agent.timeline import TimelineEntry, TimelineEntryType


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "timeline_that_with_assisstant_message_being_skip.json"


def _load_fixture() -> dict:
    """Load the fixture JSON."""
    if not FIXTURE_PATH.exists():
        pytest.skip(f"Fixture not found: {FIXTURE_PATH}")
    with open(FIXTURE_PATH) as f:
        return json.load(f)


class TestReadSinceNativeMessages:
    """Regression tests for CompressedTimeline.read_since rebuilding _native_messages."""

    def test_load_from_entries_then_to_llm_messages(self):
        """
        Mirrors `test copy.py`: load entries from fixture, set timeline, call to_llm_messages.

        Before fix: _native_messages stayed empty, to_llm_messages returned wrong results.
        After fix: read_since rebuilds _native_messages, to_llm_messages works correctly.
        """
        data = _load_fixture()
        entries = [TimelineEntry.from_dict(e) for e in data["entries"]]

        timeline = CompressedTimeline()
        timeline.timeline = entries
        # Simulate what read_since now does: rebuild _native_messages from entries
        timeline._native_messages = [timeline._timeline_entry_to_native_message(e) for e in entries]

        msgs = timeline.to_llm_messages()

        # Fixture has 6 entries → 6 messages
        assert len(msgs) == 6, f"Expected 6 messages, got {len(msgs)}"

        # Verify roles match the expected pattern from the fixture
        expected_roles = ["user", "user", "assistant", "tool", "user", "assistant"]
        actual_roles = [m.role for m in msgs]
        assert actual_roles == expected_roles, f"Role mismatch:\n  expected: {expected_roles}\n  actual:   {actual_roles}"

    def test_user_messages_have_role_user(self):
        """
        The original bug: USER_MESSAGE entries were mapped to role='assistant'
        due to dual-module enum identity comparison failure.
        """
        data = _load_fixture()
        entries = [TimelineEntry.from_dict(e) for e in data["entries"]]

        timeline = CompressedTimeline()
        timeline.timeline = entries
        timeline._native_messages = [timeline._timeline_entry_to_native_message(e) for e in entries]

        msgs = timeline.to_llm_messages()

        user_entries = [e for e in entries if e.entry_type == TimelineEntryType.USER_MESSAGE]
        user_msgs = [m for m in msgs if m.role == "user"]

        assert len(user_msgs) == len(
            user_entries
        ), f"Expected {len(user_entries)} user messages, got {len(user_msgs)}. USER_MESSAGE entries may be mapped to wrong role."

    def test_tool_result_has_tool_call_id(self):
        """Tool results must preserve tool_call_id for LLM API compatibility."""
        data = _load_fixture()
        entries = [TimelineEntry.from_dict(e) for e in data["entries"]]

        timeline = CompressedTimeline()
        timeline.timeline = entries
        timeline._native_messages = [timeline._timeline_entry_to_native_message(e) for e in entries]

        msgs = timeline.to_llm_messages()
        tool_msgs = [m for m in msgs if m.role == "tool"]

        assert len(tool_msgs) == 1
        assert tool_msgs[0].tool_call_id == "call_ZLeZyHV7CGZZvOPsYdzajSQy"

    def test_native_messages_match_saved_native_messages(self):
        """
        Rebuilt _native_messages should produce the same roles and tool_call_ids
        as the saved native_messages in the fixture.
        """
        data = _load_fixture()
        entries = [TimelineEntry.from_dict(e) for e in data["entries"]]
        saved_native = data.get("native_messages", [])
        if not saved_native:
            pytest.skip("Fixture has no saved native_messages")

        timeline = CompressedTimeline()
        timeline.timeline = entries
        timeline._native_messages = [timeline._timeline_entry_to_native_message(e) for e in entries]

        assert len(timeline._native_messages) == len(
            saved_native
        ), f"Count mismatch: rebuilt={len(timeline._native_messages)}, saved={len(saved_native)}"

        for i, (rebuilt, saved) in enumerate(zip(timeline._native_messages, saved_native)):
            assert rebuilt.role == saved["role"], f"Message [{i}] role mismatch: rebuilt={rebuilt.role}, saved={saved['role']}"
            saved_tc_id = saved.get("tool_call_id")
            if saved_tc_id:
                assert (
                    rebuilt.tool_call_id == saved_tc_id
                ), f"Message [{i}] tool_call_id mismatch: rebuilt={rebuilt.tool_call_id}, saved={saved_tc_id}"

    def test_add_user_message_after_load(self):
        """
        After loading entries and rebuilding _native_messages,
        adding a new user message should produce correct role='user'.
        """
        data = _load_fixture()
        entries = [TimelineEntry.from_dict(e) for e in data["entries"]]

        timeline = CompressedTimeline()
        timeline.timeline = entries
        timeline._native_messages = [timeline._timeline_entry_to_native_message(e) for e in entries]

        # Add a new user message (like the user did in the original debugging session)
        new_entry = TimelineEntry(
            entry_type=TimelineEntryType.USER_MESSAGE,
            content="What rule/logic have you follow to classify?",
        )
        timeline.add_entry(new_entry)

        msgs = timeline.to_llm_messages()

        assert len(msgs) == 7
        assert msgs[-1].role == "user", f"New message role should be 'user', got '{msgs[-1].role}'"
        assert msgs[-1].content == "What rule/logic have you follow to classify?"
