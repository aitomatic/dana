"""
Dana Reminder System - Soft guidance injection for LLM prompts.

Reminders mutate the messages list directly, giving each reminder full control
over WHERE it injects content (append, prepend, insert into specific messages, etc.).
Validity is checked lazily at evaluation time, not registration.

Main components:
- Reminder: Protocol for reminder implementations
- ReminderManager: Manages reminder registration and evaluation

Built-in reminders:
- TodoNeverCalledReminder: Nudges agent to start using todo tracking
- TodoUpdateReminder: Nudges agent to update todo list after activity

Example usage:
    >>> from dana.core.reminder import Reminder, ReminderManager
    >>>
    >>> class MyReminder:
    ...     name = "my_reminder"
    ...
    ...     def evaluate(self, agent, messages) -> None:
    ...         if some_condition:
    ...             messages.append(LLMMessage(
    ...                 role="user",
    ...                 content="<system-reminder>\\nRemember to do the thing.\\n</system-reminder>"
    ...             ))
    >>>
    >>> manager = ReminderManager()
    >>> manager.add(MyReminder())
    >>> manager.evaluate_all(agent, messages)  # reminders mutate messages in place
"""

from .base import Reminder
from .manager import ReminderManager
from .rules.builtin import SkillReminder, TodoNeverCalledReminder, TodoUpdateReminder


__all__ = [
    # Core types
    "Reminder",
    # Manager
    "ReminderManager",
    # Built-in reminders
    "SkillReminder",
    "TodoNeverCalledReminder",
    "TodoUpdateReminder",
]
