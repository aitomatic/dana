"""
Agent Events System

This module provides event handling capabilities for agents, including logging
with callback support for custom event processing.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from dana import DANA_LOGGER

if TYPE_CHECKING:
    from dana.builtin_types.agent.agent_instance import AgentInstance


class AgentEventMixin:
    # Global callback registry for log events
    _log_callbacks: list[Callable[[str, str, Any], None]] = []

    def __init__(self):
        """Initialize the AgentEventMixin."""
        self._log_callbacks = []

    def __enter__(self):
        """Enter the context of the AgentEventMixin."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context of the AgentEventMixin."""
        del self._log_callbacks

    def register_log_callback(self, callback: Callable[[str, str, Any], None]) -> None:
        """Register a callback function to be called when log() is invoked.

        Args:
            callback: Function to call with signature (agent_name, message, context)
        """
        if not callable(callback):
            raise ValueError("Callback must be callable")
        self._log_callbacks.append(callback)

    def unregister_log_callback(self, callback: Callable[[str, str, Any], None]) -> None:
        """Unregister a previously registered log callback.

        Args:
            callback: The callback function to remove
        """
        if callback in self._log_callbacks:
            self._log_callbacks.remove(callback)

    def _notify_log_callbacks(self, message: str, level: str, context: Any) -> None:
        """Notify all registered log callbacks.

        Args:
            message: The log message
            level: The log level
            context: Additional context (e.g., sandbox context)
        """
        DANA_LOGGER.debug(f"Notifying {len(self._log_callbacks)} log callbacks")
        self = cast("AgentInstance", self)
        for callback in self._log_callbacks:
            try:
                callback(self.name, message, context)
            except Exception as e:
                # Don't let callback errors break logging
                DANA_LOGGER.warning(f"[Agent {self.name}] Log callback error: {e}")

    def on_log(self, callback: Callable[[str, str, Any], None]) -> None:
        """Register a callback to be called each time log() is called.

        This is a convenience function that delegates to register_log_callback().

        Args:
            callback: Function to call with signature (agent_name, message, context)
        """
        self.register_log_callback(callback)
