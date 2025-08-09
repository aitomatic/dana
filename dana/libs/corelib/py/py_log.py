"""
Logging function for Dana standard library.

This module provides the log function for logging messages.
"""

__all__ = ["py_log"]

from typing import Any

from dana.common.utils import DANA_LOGGER
from dana.core.lang.sandbox_context import SandboxContext


def py_log(
    context: SandboxContext,
    message: Any,
    level: str = "INFO",
) -> None:
    """Log a message with the specified level.

    Args:
        context: The execution context
        message: The message to log
        level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        None

    Examples:
        log("Hello world") -> logs "Hello world" at INFO level
        log("Error occurred", "ERROR") -> logs "Error occurred" at ERROR level
    """
    if not isinstance(message, str):
        message = str(message)
        # raise TypeError("log message must be a string")

    level = level.upper()
    if level == "DEBUG":
        DANA_LOGGER.debug(message)
    elif level == "INFO":
        DANA_LOGGER.info(message)
    elif level == "WARNING":
        DANA_LOGGER.warning(message)
    elif level == "ERROR":
        DANA_LOGGER.error(message)
    elif level == "CRITICAL":
        DANA_LOGGER.critical(message)
    else:
        DANA_LOGGER.info(message)
