"""
Base protocol for the reminder system.

Reminders are evaluated lazily at runtime - validity checks happen during
evaluate(), not during registration. This eliminates the need for reload logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent
    from dana.core.agent.timeline import Timeline


@runtime_checkable
class Reminder(Protocol):
    """
    Protocol defining the interface for reminder implementations.

    Reminders are evaluated lazily - they check their own validity during
    evaluate() and return None if they shouldn't fire. This is simpler than
    checking validity at registration time.

    Attributes:
        name: Unique identifier for this reminder

    Example implementation:
        >>> class TodoReminder:
        ...     name = "todo"
        ...
        ...     def evaluate(self, agent: STARAgent, timeline: Timeline) -> str | None:
        ...         # Lazy validity check
        ...         todo_resource = self._get_todo_resource(agent)
        ...         if not todo_resource:
        ...             return None  # Skip - no todo resource
        ...
        ...         # Trigger logic
        ...         if not self._should_trigger(timeline):
        ...             return None
        ...
        ...         # Generate prompt
        ...         return "Remember to update todos."
    """

    name: str

    def evaluate(self, agent: STARAgent, timeline: Timeline) -> str | None:
        """
        Evaluate this reminder and return prompt to inject, or None to skip.

        This single method handles:
        1. Validity checking (e.g., does agent have required resources?)
        2. Trigger condition checking (e.g., has enough turns passed?)
        3. Prompt generation

        Args:
            agent: The STARAgent instance
            timeline: The current timeline

        Returns:
            Prompt string to inject, or None if reminder shouldn't fire
        """
        ...
