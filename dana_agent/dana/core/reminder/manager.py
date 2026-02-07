"""
ReminderManager - Manages reminder evaluation and generation.

Simplified design:
- Reminders check validity lazily in evaluate(), not at registration
- evaluate_all() passes messages to each reminder for direct mutation
- No reload_builtins() needed - validity is checked at evaluation time
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from dana.common.llm.types import LLMMessage

from .base import Reminder


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent

logger = structlog.get_logger()


class ReminderManager:
    """
    Manages reminder registration and evaluation.

    Simplified design:
    - No agent parameter needed at construction (validity is lazy)
    - evaluate_all() passes messages to each reminder for in-place mutation
    - add()/remove() for managing reminders

    Example:
        >>> manager = ReminderManager()
        >>> manager.add(TodoReminder())
        >>> manager.evaluate_all(agent, messages)  # reminders mutate messages in place
    """

    def __init__(self, load_builtins: bool = True):
        """
        Initialize the ReminderManager.

        Args:
            load_builtins: Whether to load built-in reminders (default: True)
        """
        self._reminders: list[Reminder] = []

        if load_builtins:
            self._load_builtins()

    def _load_builtins(self) -> None:
        """Load built-in reminders."""
        from .rules.builtin import get_builtin_reminders

        for reminder in get_builtin_reminders():
            self._reminders.append(reminder)

        logger.debug(
            "reminder_manager_initialized",
            reminder_count=len(self._reminders),
            reminder_names=[r.name for r in self._reminders],
        )

    def add(self, reminder: Reminder) -> None:
        """
        Add a reminder.

        Args:
            reminder: Any object matching Reminder protocol
        """
        self._reminders.append(reminder)
        logger.debug("reminder_added", name=reminder.name)

    # Alias for backward compatibility
    register = add

    def remove(self, name: str) -> bool:
        """
        Remove a reminder by name.

        Args:
            name: The name of the reminder to remove

        Returns:
            True if the reminder was found and removed, False otherwise
        """
        original_count = len(self._reminders)
        self._reminders = [r for r in self._reminders if r.name != name]
        removed = len(self._reminders) < original_count

        if removed:
            logger.debug("reminder_removed", name=name)

        return removed

    @property
    def reminders(self) -> list[Reminder]:
        """Get the list of registered reminders."""
        return self._reminders

    def evaluate_all(self, agent: STARAgent, messages: list[LLMMessage]) -> None:
        """
        Evaluate all reminders, letting each mutate the messages list.

        Each reminder's evaluate() method handles:
        - Validity checking (e.g., does agent have required resources?)
        - Trigger condition checking
        - Message mutation (appending, inserting, etc.)

        Args:
            agent: The STARAgent instance
            messages: The messages list for reminders to mutate in place
        """
        for reminder in self._reminders:
            try:
                reminder.evaluate(agent, messages)
            except Exception as e:
                logger.warning(
                    "reminder_evaluate_error",
                    name=reminder.name,
                    error=str(e),
                )
