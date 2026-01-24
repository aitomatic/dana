"""
Tests for the simplified system reminder mechanism.

Tests cover:
- Reminder protocol conformance
- ReminderManager add/remove and evaluate_all
- Built-in reminders (TodoNeverCalled, TodoUpdate) with lazy validity
- Integration verification
"""

from unittest.mock import MagicMock

from dana.core.reminder import (
    Reminder,
    ReminderManager,
)
from dana.core.reminder.rules.builtin import (
    TodoNeverCalledReminder,
    TodoUpdateReminder,
    get_builtin_reminders,
)


class TestReminderProtocol:
    """Tests for Reminder protocol conformance."""

    def test_custom_reminder_protocol_conformance(self):
        """Test that a custom class conforms to Reminder protocol."""

        class MyReminder:
            name = "my_reminder"

            def evaluate(self, agent, timeline) -> str | None:
                return "Test reminder."

        reminder = MyReminder()
        assert isinstance(reminder, Reminder)

    def test_builtin_reminders_protocol_conformance(self):
        """Test that builtin reminders conform to Reminder protocol."""
        reminders = get_builtin_reminders()

        for reminder in reminders:
            assert hasattr(reminder, "name")
            assert hasattr(reminder, "evaluate")
            assert callable(reminder.evaluate)


class TestReminderManager:
    """Tests for ReminderManager."""

    def test_create_manager_without_builtin(self):
        """Test creating a manager without built-in reminders."""
        manager = ReminderManager(load_builtins=False)

        assert len(manager.reminders) == 0

    def test_create_manager_with_builtins(self):
        """Test creating a manager with built-in reminders."""
        manager = ReminderManager(load_builtins=True)

        # Should have the todo reminders loaded
        names = [r.name for r in manager.reminders]
        assert "todo_never_called" in names
        assert "todo_update" in names

    def test_add_reminder(self):
        """Test adding a custom reminder."""
        manager = ReminderManager(load_builtins=False)

        class MyReminder:
            name = "custom"

            def evaluate(self, agent, timeline) -> str | None:
                return "Custom reminder."

        manager.add(MyReminder())

        assert len(manager.reminders) == 1
        assert manager.reminders[0].name == "custom"

    def test_register_alias(self):
        """Test that register() is an alias for add()."""
        manager = ReminderManager(load_builtins=False)

        class MyReminder:
            name = "test"

            def evaluate(self, agent, timeline) -> str | None:
                return None

        manager.register(MyReminder())

        assert len(manager.reminders) == 1

    def test_remove_reminder(self):
        """Test removing a reminder by name."""
        manager = ReminderManager(load_builtins=False)

        class MyReminder:
            name = "to_remove"

            def evaluate(self, agent, timeline) -> str | None:
                return None

        manager.add(MyReminder())
        result = manager.remove("to_remove")

        assert result is True
        assert len(manager.reminders) == 0

    def test_remove_nonexistent(self):
        """Test removing a reminder that doesn't exist."""
        manager = ReminderManager(load_builtins=False)

        result = manager.remove("nonexistent")

        assert result is False

    def test_evaluate_all_returns_xml(self):
        """Test that evaluate_all returns properly formatted XML."""
        manager = ReminderManager(load_builtins=False)

        class AlwaysReminder:
            name = "always"

            def evaluate(self, agent, timeline) -> str | None:
                return "Always triggers."

        manager.add(AlwaysReminder())

        mock_agent = MagicMock()
        mock_timeline = MagicMock()

        result = manager.evaluate_all(mock_agent, mock_timeline)

        assert "<system-reminder>" in result
        assert "</system-reminder>" in result
        assert "Always triggers." in result

    def test_evaluate_all_empty_when_nothing_triggers(self):
        """Test that evaluate_all returns empty string when no reminders trigger."""
        manager = ReminderManager(load_builtins=False)

        class NeverReminder:
            name = "never"

            def evaluate(self, agent, timeline) -> str | None:
                return None

        manager.add(NeverReminder())

        mock_agent = MagicMock()
        mock_timeline = MagicMock()

        result = manager.evaluate_all(mock_agent, mock_timeline)

        assert result == ""

    def test_evaluate_all_multiple_reminders(self):
        """Test evaluate_all with multiple triggering reminders."""
        manager = ReminderManager(load_builtins=False)

        class FirstReminder:
            name = "first"

            def evaluate(self, agent, timeline) -> str | None:
                return "First reminder."

        class SecondReminder:
            name = "second"

            def evaluate(self, agent, timeline) -> str | None:
                return "Second reminder."

        manager.add(FirstReminder())
        manager.add(SecondReminder())

        mock_agent = MagicMock()
        mock_timeline = MagicMock()

        result = manager.evaluate_all(mock_agent, mock_timeline)

        assert "First reminder." in result
        assert "Second reminder." in result
        # Each should be in its own system-reminder tag
        assert result.count("<system-reminder>") == 2

    def test_evaluate_all_handles_exceptions(self):
        """Test that evaluate_all handles exceptions gracefully."""
        manager = ReminderManager(load_builtins=False)

        class BadReminder:
            name = "bad"

            def evaluate(self, agent, timeline) -> str | None:
                raise ValueError("Something went wrong")

        class GoodReminder:
            name = "good"

            def evaluate(self, agent, timeline) -> str | None:
                return "Good reminder."

        manager.add(BadReminder())
        manager.add(GoodReminder())

        mock_agent = MagicMock()
        mock_timeline = MagicMock()

        # Should not raise, and should still return the good reminder
        result = manager.evaluate_all(mock_agent, mock_timeline)

        assert "Good reminder." in result


class TestTodoNeverCalledReminder:
    """Tests for TodoNeverCalledReminder with lazy validity."""

    def test_returns_none_without_todo_resource(self):
        """Test that reminder returns None when agent has no ToDoResource."""
        reminder = TodoNeverCalledReminder()
        mock_agent = MagicMock()
        mock_agent._resources = []  # No resources
        mock_agent._star_loop_count = 5

        mock_timeline = MagicMock()
        mock_timeline.timeline = []

        result = reminder.evaluate(mock_agent, mock_timeline)

        assert result is None

    def test_returns_none_before_threshold(self):
        """Test that reminder returns None before turn threshold."""
        from dana.core.resource.todo_resource import ToDoResource

        reminder = TodoNeverCalledReminder(turns_threshold=2)
        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._star_loop_count = 1  # Below threshold

        mock_timeline = MagicMock()
        mock_timeline.timeline = []

        result = reminder.evaluate(mock_agent, mock_timeline)

        assert result is None

    def test_triggers_after_threshold_no_todo_calls(self):
        """Test that reminder triggers after threshold with no todo_write calls."""
        from dana.core.agent.timeline import TimelineEntry, TimelineEntryType
        from dana.core.resource.todo_resource import ToDoResource

        reminder = TodoNeverCalledReminder(turns_threshold=2)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._star_loop_count = 3  # Above threshold

        mock_timeline = MagicMock()
        mock_timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test"),
            TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="response"),
        ]

        result = reminder.evaluate(mock_agent, mock_timeline)

        assert result is not None
        assert "ToDoResource" in result
        assert "todo_write" in result

    def test_returns_none_if_todo_write_called(self):
        """Test that reminder returns None if todo_write was called."""
        from dana.core.agent.timeline import TimelineEntry, TimelineEntryType
        from dana.core.resource.todo_resource import ToDoResource

        reminder = TodoNeverCalledReminder(turns_threshold=2)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._star_loop_count = 3

        mock_timeline = MagicMock()
        mock_timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.TOOL_CALL, content="todo_write(todos=[...])"),
        ]

        result = reminder.evaluate(mock_agent, mock_timeline)

        assert result is None


class TestTodoUpdateReminder:
    """Tests for TodoUpdateReminder with lazy validity."""

    def test_returns_none_without_todo_resource(self):
        """Test that reminder returns None when agent has no ToDoResource."""
        reminder = TodoUpdateReminder()
        mock_agent = MagicMock()
        mock_agent._resources = []  # No resources

        mock_timeline = MagicMock()
        mock_timeline.timeline = []

        result = reminder.evaluate(mock_agent, mock_timeline)

        assert result is None

    def test_returns_none_if_never_called(self):
        """Test that reminder returns None if todo_write was never called."""
        from dana.core.agent.timeline import TimelineEntry, TimelineEntryType
        from dana.core.resource.todo_resource import ToDoResource

        reminder = TodoUpdateReminder(turns_threshold=3)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]

        mock_timeline = MagicMock()
        mock_timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test"),
            TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="response"),
        ]

        result = reminder.evaluate(mock_agent, mock_timeline)

        assert result is None

    def test_triggers_after_turns_since_last_call(self):
        """Test that reminder triggers after N turns since last todo_write call."""
        from dana.core.agent.timeline import TimelineEntry, TimelineEntryType
        from dana.core.resource.todo_resource import ToDoResource

        reminder = TodoUpdateReminder(turns_threshold=2, tokens_threshold=10000)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]

        mock_timeline = MagicMock()
        # todo_write called, then 4 more entries (2 turns worth)
        mock_timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.TOOL_CALL, content="todo_write(todos=[...])"),
            TimelineEntry(entry_type=TimelineEntryType.RESOURCE_RESULT, content="result"),
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test1"),
            TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="response1"),
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test2"),
            TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="response2"),
        ]

        result = reminder.evaluate(mock_agent, mock_timeline)

        assert result is not None
        assert "todo list" in result.lower()

    def test_triggers_after_tokens_since_last_call(self):
        """Test that reminder triggers after K tokens since last todo_write call."""
        from dana.core.agent.timeline import TimelineEntry, TimelineEntryType
        from dana.core.resource.todo_resource import ToDoResource

        reminder = TodoUpdateReminder(turns_threshold=100, tokens_threshold=100)  # High turns, low tokens

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]

        mock_timeline = MagicMock()
        # todo_write called, then entries with lots of content
        mock_timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.TOOL_CALL, content="todo_write(todos=[...])"),
            TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="x" * 500),  # ~125 tokens
        ]

        result = reminder.evaluate(mock_agent, mock_timeline)

        assert result is not None

    def test_returns_none_if_recently_called(self):
        """Test that reminder returns None if todo_write was recently called."""
        from dana.core.agent.timeline import TimelineEntry, TimelineEntryType
        from dana.core.resource.todo_resource import ToDoResource

        reminder = TodoUpdateReminder(turns_threshold=5, tokens_threshold=5000)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]

        mock_timeline = MagicMock()
        # todo_write called recently
        mock_timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.TOOL_CALL, content="todo_write(todos=[...])"),
            TimelineEntry(entry_type=TimelineEntryType.RESOURCE_RESULT, content="result"),
        ]

        result = reminder.evaluate(mock_agent, mock_timeline)

        assert result is None


class TestGetBuiltinReminders:
    """Tests for get_builtin_reminders function."""

    def test_returns_list(self):
        """Test that it returns a list of reminders."""
        reminders = get_builtin_reminders()

        assert isinstance(reminders, list)
        assert len(reminders) == 2

    def test_returns_todo_reminders(self):
        """Test that it returns the todo reminders."""
        reminders = get_builtin_reminders()
        names = [r.name for r in reminders]

        assert "todo_never_called" in names
        assert "todo_update" in names

    def test_reminders_have_evaluate(self):
        """Test that all returned reminders have evaluate method."""
        reminders = get_builtin_reminders()

        for reminder in reminders:
            assert hasattr(reminder, "evaluate")
            assert callable(reminder.evaluate)


class TestLazyValidityBehavior:
    """Tests for the lazy validity checking behavior."""

    def test_reminders_auto_skip_without_resource(self):
        """Test that reminders auto-skip when resource is not present."""
        # This is the key behavior change - reminders check validity lazily
        manager = ReminderManager(load_builtins=True)

        mock_agent = MagicMock()
        mock_agent._resources = []  # No ToDoResource
        mock_agent._star_loop_count = 5

        mock_timeline = MagicMock()
        mock_timeline.timeline = []

        # Even though todo reminders are loaded, they should auto-skip
        result = manager.evaluate_all(mock_agent, mock_timeline)

        assert result == ""  # No reminders fired

    def test_reminders_fire_when_resource_present(self):
        """Test that reminders fire when resource is present."""
        from dana.core.agent.timeline import TimelineEntry, TimelineEntryType
        from dana.core.resource.todo_resource import ToDoResource

        manager = ReminderManager(load_builtins=True)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._star_loop_count = 5

        mock_timeline = MagicMock()
        mock_timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test"),
        ]

        result = manager.evaluate_all(mock_agent, mock_timeline)

        # TodoNeverCalledReminder should fire (no todo_write calls)
        assert "ToDoResource" in result
