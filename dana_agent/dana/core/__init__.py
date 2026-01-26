"""
Core module for the Adana agentic architecture.

This module provides the core components for building conversational AI agents
with resource and workflow management.
"""

__all__ = [
    "STARAgent",
    "Reminder",
    "ReminderManager",
]


def __getattr__(name: str):
    if name == "STARAgent":
        from .agent import STARAgent

        return STARAgent

    # Reminder system exports
    if name in ("Reminder", "ReminderManager"):
        from .reminder import Reminder, ReminderManager

        return {
            "Reminder": Reminder,
            "ReminderManager": ReminderManager,
        }[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
