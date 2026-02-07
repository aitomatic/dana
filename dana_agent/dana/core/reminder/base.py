"""
Base protocol for the reminder system.

Reminders mutate the messages list directly, giving each reminder full control
over WHERE it injects content (append, prepend, insert into specific messages, etc.).
Validity checks happen during evaluate(), not during registration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from dana.common.llm.types import LLMMessage


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent


@runtime_checkable
class Reminder(Protocol):
    """
    Protocol defining the interface for reminder implementations.

    Reminders are evaluated lazily - they check their own validity during
    evaluate() and skip (no mutation) if they shouldn't fire. Each reminder
    has full control over message placement by mutating the messages list directly.

    Attributes:
        name: Unique identifier for this reminder

    Example implementation:
        >>> class TodoReminder:
        ...     name = "todo"
        ...
        ...     def evaluate(self, agent: STARAgent, messages: list[LLMMessage]) -> None:
        ...         # Lazy validity check
        ...         todo_resource = self._get_todo_resource(agent)
        ...         if not todo_resource:
        ...             return  # Skip - no todo resource
        ...
        ...         # Trigger logic
        ...         if not self._should_trigger(agent):
        ...             return
        ...
        ...         # Mutate messages — each reminder wraps its own XML
        ...         messages.append(LLMMessage(
        ...             role="user",
        ...             content="<system-reminder>\\nRemember to update todos.\\n</system-reminder>"
        ...         ))
    """

    name: str

    def evaluate(self, agent: STARAgent, messages: list[LLMMessage]) -> None:
        """
        Evaluate this reminder and mutate messages if it should fire.

        This single method handles:
        1. Validity checking (e.g., does agent have required resources?)
        2. Trigger condition checking (e.g., has enough turns passed?)
        3. Message mutation (appending, inserting, etc.)

        Args:
            agent: The STARAgent instance
            messages: The messages list to mutate in place
        """
        ...
