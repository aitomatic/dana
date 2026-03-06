"""
Tests for the simplified system reminder mechanism.

Tests cover:
- Reminder protocol conformance
- ReminderManager add/remove and evaluate_all (messages-based mutation)
- Built-in reminders (TodoNeverCalled, TodoUpdate) with lazy validity
- Integration verification
"""

from pathlib import Path
from unittest.mock import MagicMock

from dana.common.llm.types import LLMMessage
from dana.core.reminder import (
    Reminder,
    ReminderManager,
)
from dana.core.reminder.rules.builtin import (
    SkillReminder,
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

            def evaluate(self, agent, messages: list[LLMMessage]) -> None:
                messages.append(LLMMessage(role="user", content="Test reminder."))

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

            def evaluate(self, agent, messages: list[LLMMessage]) -> None:
                messages.append(LLMMessage(role="user", content="Custom reminder."))

        manager.add(MyReminder())

        assert len(manager.reminders) == 1
        assert manager.reminders[0].name == "custom"

    def test_register_alias(self):
        """Test that register() is an alias for add()."""
        manager = ReminderManager(load_builtins=False)

        class MyReminder:
            name = "test"

            def evaluate(self, agent, messages: list[LLMMessage]) -> None:
                pass

        manager.register(MyReminder())

        assert len(manager.reminders) == 1

    def test_remove_reminder(self):
        """Test removing a reminder by name."""
        manager = ReminderManager(load_builtins=False)

        class MyReminder:
            name = "to_remove"

            def evaluate(self, agent, messages: list[LLMMessage]) -> None:
                pass

        manager.add(MyReminder())
        result = manager.remove("to_remove")

        assert result is True
        assert len(manager.reminders) == 0

    def test_remove_nonexistent(self):
        """Test removing a reminder that doesn't exist."""
        manager = ReminderManager(load_builtins=False)

        result = manager.remove("nonexistent")

        assert result is False

    def test_evaluate_all_mutates_messages(self):
        """Test that evaluate_all mutates the messages list."""
        manager = ReminderManager(load_builtins=False)

        class AlwaysReminder:
            name = "always"

            def evaluate(self, agent, messages: list[LLMMessage]) -> None:
                messages.append(LLMMessage(role="user", content="<system-reminder>\nAlways triggers.\n</system-reminder>"))

        manager.add(AlwaysReminder())

        mock_agent = MagicMock()
        messages = [LLMMessage(role="user", content="Hello")]

        manager.evaluate_all(mock_agent, messages)

        assert len(messages) == 2
        assert "<system-reminder>" in messages[1].content
        assert "Always triggers." in messages[1].content

    def test_evaluate_all_no_mutation_when_nothing_triggers(self):
        """Test that evaluate_all leaves messages unchanged when no reminders trigger."""
        manager = ReminderManager(load_builtins=False)

        class NeverReminder:
            name = "never"

            def evaluate(self, agent, messages: list[LLMMessage]) -> None:
                pass  # Does nothing — no mutation

        manager.add(NeverReminder())

        mock_agent = MagicMock()
        messages = [LLMMessage(role="user", content="Hello")]

        manager.evaluate_all(mock_agent, messages)

        assert len(messages) == 1  # Unchanged

    def test_evaluate_all_multiple_reminders(self):
        """Test evaluate_all with multiple triggering reminders."""
        manager = ReminderManager(load_builtins=False)

        class FirstReminder:
            name = "first"

            def evaluate(self, agent, messages: list[LLMMessage]) -> None:
                messages.append(LLMMessage(role="user", content="<system-reminder>\nFirst reminder.\n</system-reminder>"))

        class SecondReminder:
            name = "second"

            def evaluate(self, agent, messages: list[LLMMessage]) -> None:
                messages.append(LLMMessage(role="user", content="<system-reminder>\nSecond reminder.\n</system-reminder>"))

        manager.add(FirstReminder())
        manager.add(SecondReminder())

        mock_agent = MagicMock()
        messages = [LLMMessage(role="user", content="Hello")]

        manager.evaluate_all(mock_agent, messages)

        assert len(messages) == 3  # Original + 2 appended
        assert "First reminder." in messages[1].content
        assert "Second reminder." in messages[2].content

    def test_evaluate_all_handles_exceptions(self):
        """Test that evaluate_all handles exceptions gracefully."""
        manager = ReminderManager(load_builtins=False)

        class BadReminder:
            name = "bad"

            def evaluate(self, agent, messages: list[LLMMessage]) -> None:
                raise ValueError("Something went wrong")

        class GoodReminder:
            name = "good"

            def evaluate(self, agent, messages: list[LLMMessage]) -> None:
                messages.append(LLMMessage(role="user", content="<system-reminder>\nGood reminder.\n</system-reminder>"))

        manager.add(BadReminder())
        manager.add(GoodReminder())

        mock_agent = MagicMock()
        messages = [LLMMessage(role="user", content="Hello")]

        # Should not raise, and should still append the good reminder
        manager.evaluate_all(mock_agent, messages)

        assert len(messages) == 2
        assert "Good reminder." in messages[1].content


class TestTodoNeverCalledReminder:
    """Tests for TodoNeverCalledReminder with lazy validity."""

    def test_skips_without_todo_resource(self):
        """Test that reminder does not mutate messages when agent has no ToDoResource."""
        reminder = TodoNeverCalledReminder()
        mock_agent = MagicMock()
        mock_agent._resources = []  # No resources
        mock_agent._star_loop_count = 5
        mock_agent._timeline = MagicMock()
        mock_agent._timeline.timeline = []

        messages = [LLMMessage(role="user", content="Hello")]

        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 1  # No mutation

    def test_skips_before_threshold(self):
        """Test that reminder does not mutate messages before turn threshold."""
        from dana.core.resource.todo_resource import ToDoResource

        reminder = TodoNeverCalledReminder(turns_threshold=2)
        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._star_loop_count = 1  # Below threshold
        mock_agent._timeline = MagicMock()
        mock_agent._timeline.timeline = []

        messages = [LLMMessage(role="user", content="Hello")]

        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 1  # No mutation

    def test_triggers_after_threshold_no_todo_calls(self):
        """Test that reminder appends message after threshold with no todo_write calls."""
        from dana.core.resource.todo_resource import ToDoResource
        from dana.core.timeline.timeline import TimelineEntry, TimelineEntryType

        reminder = TodoNeverCalledReminder(turns_threshold=2)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._star_loop_count = 3  # Above threshold
        mock_agent._timeline = MagicMock()
        mock_agent._timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test"),
            TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="response"),
        ]

        messages = [LLMMessage(role="user", content="Hello")]

        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 2
        assert "<system-reminder>" in messages[1].content
        assert "todo list is currently empty" in messages[1].content
        assert "todo:todo_write" in messages[1].content

    def test_skips_if_todo_write_called(self):
        """Test that reminder does not mutate messages if todo_write was called."""
        from dana.core.resource.todo_resource import ToDoResource
        from dana.core.timeline.timeline import TimelineEntry, TimelineEntryType

        reminder = TodoNeverCalledReminder(turns_threshold=2)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._star_loop_count = 3
        mock_agent._timeline = MagicMock()
        mock_agent._timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.TOOL_CALL, content="todo_write(todos=[...])"),
        ]

        messages = [LLMMessage(role="user", content="Hello")]

        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 1  # No mutation


class TestTodoUpdateReminder:
    """Tests for TodoUpdateReminder with lazy validity."""

    def test_skips_without_todo_resource(self):
        """Test that reminder does not mutate messages when agent has no ToDoResource."""
        reminder = TodoUpdateReminder()
        mock_agent = MagicMock()
        mock_agent._resources = []  # No resources
        mock_agent._timeline = MagicMock()
        mock_agent._timeline.timeline = []

        messages = [LLMMessage(role="user", content="Hello")]

        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 1  # No mutation

    def test_skips_if_never_called(self):
        """Test that reminder does not mutate messages if todo_write was never called."""
        from dana.core.resource.todo_resource import ToDoResource
        from dana.core.timeline.timeline import TimelineEntry, TimelineEntryType

        reminder = TodoUpdateReminder(turns_threshold=3)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._timeline = MagicMock()
        mock_agent._timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test"),
            TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="response"),
        ]

        messages = [LLMMessage(role="user", content="Hello")]

        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 1  # No mutation

    def test_triggers_after_turns_since_last_call(self):
        """Test that reminder appends message after N turns since last todo_write call."""
        from dana.core.resource.todo_resource import ToDoResource
        from dana.core.timeline.timeline import TimelineEntry, TimelineEntryType

        reminder = TodoUpdateReminder(turns_threshold=2, tokens_threshold=10000)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._timeline = MagicMock()
        # todo_write called, then 4 more entries (2 turns worth)
        mock_agent._timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.TOOL_CALL, content="todo_write(todos=[...])"),
            TimelineEntry(entry_type=TimelineEntryType.RESOURCE_RESULT, content="result"),
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test1"),
            TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="response1"),
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test2"),
            TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="response2"),
        ]

        messages = [LLMMessage(role="user", content="Hello")]

        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 2
        assert "<system-reminder>" in messages[1].content
        assert "todo list" in messages[1].content.lower()

    def test_triggers_after_tokens_since_last_call(self):
        """Test that reminder appends message after K tokens since last todo_write call."""
        from dana.core.resource.todo_resource import ToDoResource
        from dana.core.timeline.timeline import TimelineEntry, TimelineEntryType

        reminder = TodoUpdateReminder(turns_threshold=100, tokens_threshold=100)  # High turns, low tokens

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._timeline = MagicMock()
        # todo_write called, then entries with lots of content
        mock_agent._timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.TOOL_CALL, content="todo_write(todos=[...])"),
            TimelineEntry(entry_type=TimelineEntryType.AGENT_RESPONSE, content="x" * 500),  # ~125 tokens
        ]

        messages = [LLMMessage(role="user", content="Hello")]

        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 2

    def test_skips_if_recently_called(self):
        """Test that reminder does not mutate messages if todo_write was recently called."""
        from dana.core.resource.todo_resource import ToDoResource
        from dana.core.timeline.timeline import TimelineEntry, TimelineEntryType

        reminder = TodoUpdateReminder(turns_threshold=5, tokens_threshold=5000)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._timeline = MagicMock()
        # todo_write called recently
        mock_agent._timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.TOOL_CALL, content="todo_write(todos=[...])"),
            TimelineEntry(entry_type=TimelineEntryType.RESOURCE_RESULT, content="result"),
        ]

        messages = [LLMMessage(role="user", content="Hello")]

        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 1  # No mutation


class TestGetBuiltinReminders:
    """Tests for get_builtin_reminders function."""

    def test_returns_list(self):
        """Test that it returns a list of reminders."""
        reminders = get_builtin_reminders()

        assert isinstance(reminders, list)
        assert len(reminders) == 3

    def test_returns_todo_reminders(self):
        """Test that it returns the todo reminders."""
        reminders = get_builtin_reminders()
        names = [r.name for r in reminders]

        assert "available_skills" in names
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
        manager = ReminderManager(load_builtins=True)

        mock_agent = MagicMock()
        mock_agent._resources = []  # No ToDoResource
        mock_agent._star_loop_count = 5
        mock_agent._timeline = MagicMock()
        mock_agent._timeline.timeline = []

        messages = [LLMMessage(role="user", content="Hello")]

        # Even though todo reminders are loaded, they should auto-skip
        manager.evaluate_all(mock_agent, messages)

        assert len(messages) == 1  # No reminders fired

    def test_reminders_fire_when_resource_present(self):
        """Test that reminders fire when resource is present."""
        from dana.core.resource.todo_resource import ToDoResource
        from dana.core.timeline.timeline import TimelineEntry, TimelineEntryType

        manager = ReminderManager(load_builtins=True)

        mock_agent = MagicMock()
        mock_todo_resource = MagicMock(spec=ToDoResource)
        mock_agent._resources = [mock_todo_resource]
        mock_agent._star_loop_count = 5
        mock_agent._timeline = MagicMock()
        mock_agent._timeline.timeline = [
            TimelineEntry(entry_type=TimelineEntryType.USER_MESSAGE, content="test"),
        ]

        messages = [LLMMessage(role="user", content="Hello")]

        manager.evaluate_all(mock_agent, messages)

        # TodoNeverCalledReminder should fire (no todo_write calls)
        assert len(messages) >= 2
        assert "todo list is currently empty" in messages[1].content


class TestSkillReminder:
    """Tests for SkillReminder with lazy validity."""

    def test_skips_without_skill_resource(self):
        """Test that reminder does not fire when agent has no DanaSkillResource."""
        reminder = SkillReminder()
        mock_agent = MagicMock()
        mock_agent._resources = []

        messages = [LLMMessage(role="user", content="Hello")]
        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 1  # No mutation

    def test_skips_when_no_model_invocable_skills(self):
        """Test that reminder does not fire when there are no model-invocable skills."""
        from dana.core.skills.dana_skills.skills import DanaSkillResource

        reminder = SkillReminder()
        mock_agent = MagicMock()
        mock_skill_resource = MagicMock(spec=DanaSkillResource)
        mock_skill_resource.list_model_invocable.return_value = []
        mock_agent._resources = [mock_skill_resource]

        messages = [LLMMessage(role="user", content="Hello")]
        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 1  # No mutation

    def test_fires_when_skills_available(self):
        """Test that reminder appends message when skills are available."""
        from dana.core.skills.dana_skills.models import DanaSkill
        from dana.core.skills.dana_skills.skills import DanaSkillResource

        reminder = SkillReminder()
        mock_agent = MagicMock()
        mock_skill_resource = MagicMock(spec=DanaSkillResource)
        mock_skill_resource.list_model_invocable.return_value = [
            DanaSkill(name="test-skill", description="A test skill", path=Path("/tmp/test")),
        ]
        mock_skill_resource.get_prompt_descriptions.return_value = "- test-skill: A test skill"
        mock_agent._resources = [mock_skill_resource]

        messages = [LLMMessage(role="user", content="Hello")]
        reminder.evaluate(mock_agent, messages)

        assert len(messages) == 2
        assert "<system-reminder>" in messages[1].content
        assert "test-skill" in messages[1].content
        assert "skills.invoke" in messages[1].content

    def test_reminder_content_format(self):
        """Test the format of the reminder message."""
        from dana.core.skills.dana_skills.models import DanaSkill
        from dana.core.skills.dana_skills.skills import DanaSkillResource

        reminder = SkillReminder()
        mock_agent = MagicMock()
        mock_skill_resource = MagicMock(spec=DanaSkillResource)
        mock_skill_resource.list_model_invocable.return_value = [
            DanaSkill(name="commit", description="Generate commit messages", path=Path("/tmp/test")),
            DanaSkill(name="review", description="Code review helper", path=Path("/tmp/test")),
        ]
        mock_skill_resource.get_prompt_descriptions.return_value = "- commit: Generate commit messages\n- review: Code review helper"
        mock_agent._resources = [mock_skill_resource]

        messages = [LLMMessage(role="user", content="Hello")]
        reminder.evaluate(mock_agent, messages)

        content = messages[1].content
        assert content.startswith("<system-reminder>")
        assert content.endswith("</system-reminder>")
        assert "commit" in content
        assert "review" in content
