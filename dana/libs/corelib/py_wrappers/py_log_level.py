"""
Log level function for Dana standard library.

This module provides the log_level function for setting log levels.
"""

__all__ = ["py_log_level"]

from dana.core.lang.sandbox_context import SandboxContext


def py_log_level(
    context: SandboxContext,
    level: str,
    namespace: str = "dana",
) -> None:
    """Set the logging level.

    Args:
        context: The execution context
        level: The log level to set (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        namespace: The namespace to set the level for (default: "dana")

    Returns:
        None

    Examples:
        log_level("DEBUG") -> sets logging level to DEBUG
        log_level("ERROR", "dana") -> sets logging level to ERROR for dana namespace
    """
    if not isinstance(level, str):
        raise TypeError("log_level argument must be a string")

    # Use the SandboxLogger for proper namespace-aware logging
    from dana.core.lang.log_manager import SandboxLogger

    SandboxLogger.set_log_level(level, namespace, context)
