"""
Logging function for Dana standard library.

This module provides the log function for logging messages.
"""

__all__ = ["py_log"]

import logging

from dana.core.lang.sandbox_context import SandboxContext


def py_log(
    context: SandboxContext,
    message: str,
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
        raise TypeError("log message must be a string")

    level = level.upper()
    if level == "DEBUG":
        logging.debug(message)
    elif level == "INFO":
        logging.info(message)
    elif level == "WARNING":
        logging.warning(message)
    elif level == "ERROR":
        logging.error(message)
    elif level == "CRITICAL":
        logging.critical(message)
    else:
        logging.info(message)
