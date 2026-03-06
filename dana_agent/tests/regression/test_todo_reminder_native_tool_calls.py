"""
Regression test: todo reminders must detect native tool calls (not just legacy XML).

Reproduces the bug from a real session where:
1. Agent calls todo__todo_write using native tool calling (content="" with tool_calls list)
2. TodoNeverCalledReminder._todo_write_ever_called() checks entry.content (empty string)
3. The check fails → reminder thinks todo_write was never called
4. TodoUpdateReminder._find_last_todo_write_index() has the same bug
5. Reminders keep firing every STAR loop → LLM keeps calling todo_write → infinite loop

Timeline source: tests/regression/fixtures/timeline_with_looping_todo_and_incorrect_system_reminder.json
"""

import json
from pathlib import Path

import pytest

from dana.core.timeline.timeline import TimelineEntry, TimelineEntryType
from dana.core.reminder.rules.builtin import (
    TodoNeverCalledReminder,
    TodoUpdateReminder,
    _entry_has_tool_call,
)


TIMELINE_PATH = Path(__file__).resolve().parent / "fixtures" / "timeline_with_looping_todo_and_incorrect_system_reminder.json"


def _load_timeline_data() -> dict:
    """Load the looping todo timeline JSON."""
    if not TIMELINE_PATH.exists():
        pytest.skip(f"Timeline fixture not found: {TIMELINE_PATH}")
    with open(TIMELINE_PATH) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# _entry_has_tool_call helper tests
# ---------------------------------------------------------------------------


class TestEntryHasToolCall:
    """Test the shared _entry_has_tool_call helper handles both formats."""

    def test_detects_legacy_xml_format(self):
        """Legacy XML format stores tool name in entry.content."""
        entry = TimelineEntry(
            entry_type=TimelineEntryType.TOOL_CALL,
            content='<function_call><invoke name="todo:todo_write"><parameter name="todos">...</parameter></invoke></function_call>',
        )
        assert _entry_has_tool_call(entry, "todo_write") is True

    def test_detects_native_tool_call_format(self):
        """Native format stores tool name in entry.tool_calls[].function."""
        entry = TimelineEntry(
            entry_type=TimelineEntryType.TOOL_CALL,
            content="",
            tool_calls=[
                {
                    "function": "todo__todo_write",
                    "arguments": {"todos": []},
                    "tool_call_id": "todo__todo_write_1",
                }
            ],
        )
        assert _entry_has_tool_call(entry, "todo_write") is True

    def test_detects_native_format_with_name_key(self):
        """Native format may use 'name' instead of 'function'."""
        entry = TimelineEntry(
            entry_type=TimelineEntryType.TOOL_CALL,
            content="",
            tool_calls=[
                {
                    "name": "todo__todo_write",
                    "arguments": {"todos": []},
                    "id": "call_1",
                }
            ],
        )
        assert _entry_has_tool_call(entry, "todo_write") is True

    def test_returns_false_for_unrelated_tool(self):
        """Should not match unrelated tool calls."""
        entry = TimelineEntry(
            entry_type=TimelineEntryType.TOOL_CALL,
            content="",
            tool_calls=[
                {
                    "function": "Read",
                    "arguments": {"file_path": "/some/file"},
                    "tool_call_id": "Read_1",
                }
            ],
        )
        assert _entry_has_tool_call(entry, "todo_write") is False

    def test_returns_false_for_empty_entry(self):
        """Should not match when both content and tool_calls are empty."""
        entry = TimelineEntry(
            entry_type=TimelineEntryType.TOOL_CALL,
            content="",
        )
        assert _entry_has_tool_call(entry, "todo_write") is False


# ---------------------------------------------------------------------------
# Timeline fixture tests — verifies the loop pattern exists
# ---------------------------------------------------------------------------


class TestLoopingTodoTimeline:
    """Verify the timeline fixture exhibits the looping pattern."""

    def test_timeline_has_repeated_todo_write_calls(self):
        """The fixture should contain multiple consecutive todo_write calls."""
        data = _load_timeline_data()

        todo_write_entries = []
        for entry in data["entries"]:
            if entry.get("type") != "tool_call":
                continue
            for tc in entry.get("tool_calls", []):
                func = tc.get("function", "")
                if "todo_write" in func.lower():
                    todo_write_entries.append(entry)
                    break

        # The bug caused 5+ consecutive todo_write calls
        assert len(todo_write_entries) >= 5, f"Expected at least 5 looping todo_write calls, found {len(todo_write_entries)}"

    def test_native_todo_write_entries_have_empty_content(self):
        """Confirm that native todo_write entries have content='' (the root cause)."""
        data = _load_timeline_data()

        for entry in data["entries"]:
            if entry.get("type") != "tool_call":
                continue
            for tc in entry.get("tool_calls", []):
                if "todo_write" in tc.get("function", ""):
                    assert (
                        entry["content"] == ""
                    ), "Native tool call entries should have empty content — this is what caused the reminder detection to fail"


# ---------------------------------------------------------------------------
# Reminder detection with native tool calls
# ---------------------------------------------------------------------------


class TestTodoNeverCalledReminderNativeToolCalls:
    """TodoNeverCalledReminder must detect native todo_write calls."""

    def _build_timeline_with_native_todo_write(self):
        """Build a minimal timeline that has a native todo_write call."""
        from dana.core.timeline.timeline import Timeline

        timeline = Timeline(max_context_tokens=4000)
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="Analyze this case",
            )
        )
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.TOOL_CALL,
                content="",  # Native format: empty content
                tool_calls=[
                    {
                        "function": "todo__todo_write",
                        "arguments": {"todos": [{"content": "Step 1", "status": "in_progress"}]},
                        "tool_call_id": "todo__todo_write_1",
                    }
                ],
            )
        )
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.RESOURCE_RESULT,
                content="Todo List:\n  [in_progress] Step 1",
                tool_call_id="todo__todo_write_1",
            )
        )
        return timeline

    def test_detects_native_todo_write(self):
        """_todo_write_ever_called must return True for native tool calls."""
        reminder = TodoNeverCalledReminder()
        timeline = self._build_timeline_with_native_todo_write()
        assert reminder._todo_write_ever_called(timeline) is True

    def test_detects_legacy_todo_write(self):
        """_todo_write_ever_called still works for legacy XML format."""
        from dana.core.timeline.timeline import Timeline

        reminder = TodoNeverCalledReminder()
        timeline = Timeline(max_context_tokens=4000)
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.TOOL_CALL,
                content='<function_call><invoke name="todo:todo_write"><parameter name="todos">...</parameter></invoke></function_call>',
            )
        )
        assert reminder._todo_write_ever_called(timeline) is True


class TestTodoUpdateReminderNativeToolCalls:
    """TodoUpdateReminder must find native todo_write calls."""

    def _build_timeline_with_native_todo_write(self):
        """Build a timeline with a native todo_write call at a known index."""
        from dana.core.timeline.timeline import Timeline

        timeline = Timeline(max_context_tokens=4000)
        # Index 0
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="Analyze this case",
            )
        )
        # Index 1 — the native todo_write
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.TOOL_CALL,
                content="",
                tool_calls=[
                    {
                        "function": "todo__todo_write",
                        "arguments": {"todos": [{"content": "Step 1", "status": "in_progress"}]},
                        "tool_call_id": "todo__todo_write_1",
                    }
                ],
            )
        )
        # Index 2
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.RESOURCE_RESULT,
                content="Todo List:\n  [in_progress] Step 1",
                tool_call_id="todo__todo_write_1",
            )
        )
        return timeline

    def test_finds_native_todo_write_index(self):
        """_find_last_todo_write_index must return correct index for native calls."""
        reminder = TodoUpdateReminder()
        timeline = self._build_timeline_with_native_todo_write()
        idx = reminder._find_last_todo_write_index(timeline)
        assert idx == 1, f"Expected index 1, got {idx}"

    def test_finds_legacy_todo_write_index(self):
        """_find_last_todo_write_index still works for legacy XML format."""
        from dana.core.timeline.timeline import Timeline

        reminder = TodoUpdateReminder()
        timeline = Timeline(max_context_tokens=4000)
        # Index 0
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="Do something",
            )
        )
        # Index 1
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.TOOL_CALL,
                content='<function_call><invoke name="todo:todo_write">...</invoke></function_call>',
            )
        )
        idx = reminder._find_last_todo_write_index(timeline)
        assert idx == 1

    def test_returns_negative_one_when_no_todo_write(self):
        """Should return -1 when no todo_write exists in timeline."""
        from dana.core.timeline.timeline import Timeline

        reminder = TodoUpdateReminder()
        timeline = Timeline(max_context_tokens=4000)
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="Hello",
            )
        )
        idx = reminder._find_last_todo_write_index(timeline)
        assert idx == -1
