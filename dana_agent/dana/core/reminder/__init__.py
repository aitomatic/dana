"""
Dana Reminder System - Soft guidance injection for LLM prompts.

Simplified design:
- Reminder protocol with single evaluate() method
- ReminderManager with evaluate_all() returning formatted XML
- Validity checked lazily at evaluation time, not registration

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
    ...     def evaluate(self, agent, timeline) -> str | None:
    ...         if some_condition:
    ...             return "Remember to do the thing."
    ...         return None
    >>>
    >>> manager = ReminderManager()
    >>> manager.add(MyReminder())
    >>> reminders_xml = manager.evaluate_all(agent, timeline)
"""

from .base import Reminder
from .manager import ReminderManager
from .rules.builtin import TodoNeverCalledReminder, TodoUpdateReminder


__all__ = [
    # Core types
    "Reminder",
    # Manager
    "ReminderManager",
    # Built-in reminders
    "TodoNeverCalledReminder",
    "TodoUpdateReminder",
]
