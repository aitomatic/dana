"""
ReminderManager - Manages reminder evaluation and generation.

Simplified design:
- Reminders check validity lazily in evaluate(), not at registration
- Single evaluate_all() method replaces separate evaluate() + format_reminders()
- No reload_builtins() needed - validity is checked at evaluation time
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from .base import Reminder


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent
    from dana.core.agent.timeline import Timeline

logger = structlog.get_logger()


class ReminderManager:
    """
    Manages reminder registration and evaluation.

    Simplified design:
    - No agent parameter needed at construction (validity is lazy)
    - evaluate_all() returns formatted XML directly
    - add()/remove() for managing reminders

    Example:
        >>> manager = ReminderManager()
        >>> manager.add(TodoReminder())
        >>> reminders_xml = manager.evaluate_all(agent, timeline)
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

    def evaluate_all(self, agent: STARAgent, timeline: Timeline) -> str:
        """
        Evaluate all reminders and return formatted XML.

        Each reminder's evaluate() method handles:
        - Validity checking (e.g., does agent have required resources?)
        - Trigger condition checking
        - Prompt generation

        Args:
            agent: The STARAgent instance
            timeline: The current timeline

        Returns:
            Formatted string with XML-tagged reminders, or empty string if none fired
        """
        prompts = []

        for reminder in self._reminders:
            try:
                result = reminder.evaluate(agent, timeline)
                if result:
                    prompts.append(result)
                    logger.debug("reminder_triggered", name=reminder.name)
            except Exception as e:
                logger.warning(
                    "reminder_evaluate_error",
                    name=reminder.name,
                    error=str(e),
                )

        if not prompts:
            return ""

        # Format as XML-tagged content
        formatted_parts = [f"<system-reminder>\n{prompt}\n</system-reminder>" for prompt in prompts]
        return "\n".join(formatted_parts)
