"""
Agent Events System

This module provides event handling capabilities for agents, including logging
with callback support for custom event processing.
"""

from collections.abc import Callable
from typing import Any
from dana import DANA_LOGGER

# Global callback registry for log events
_log_callbacks: list[Callable[[str, str, Any], None]] = []


def register_log_callback(callback: Callable[[str, str, Any], None]) -> None:
    """Register a callback function to be called when log() is invoked.

    Args:
        callback: Function to call with signature (agent_name, message, context)
    """
    if not callable(callback):
        raise ValueError("Callback must be callable")
    _log_callbacks.append(callback)


def unregister_log_callback(callback: Callable[[str, str, Any], None]) -> None:
    """Unregister a previously registered log callback.

    Args:
        callback: The callback function to remove
    """
    if callback in _log_callbacks:
        _log_callbacks.remove(callback)


def _notify_log_callbacks(agent_name: str, message: str, context: Any) -> None:
    """Notify all registered log callbacks.

    Args:
        agent_name: Name of the agent that logged the message
        message: The log message
        context: Additional context (e.g., sandbox context)
    """
    for callback in _log_callbacks:
        try:
            callback(agent_name, message, context)
        except Exception as e:
            # Don't let callback errors break logging
            DANA_LOGGER.warning(f"[Agent {agent_name}] Log callback error: {e}")


def on_log(callback: Callable[[str, str, Any], None]) -> None:
    """Register a callback to be called each time log() is called.

    This is a convenience function that delegates to register_log_callback().

    Args:
        callback: Function to call with signature (agent_name, message, context)
    """
    register_log_callback(callback)
