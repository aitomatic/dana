"""Log level management for DANA runtime."""

import logging
from typing import Optional

from opendxa.common.utils.logging.dxa_logger import DXA_LOGGER
from opendxa.dana.language.ast import LogLevel

# Map DANA LogLevel to Python logging levels
LEVEL_MAP = {
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.INFO: logging.INFO,
    LogLevel.WARN: logging.WARNING,
    LogLevel.ERROR: logging.ERROR
}

def set_dana_log_level(level: LogLevel) -> None:
    """Set the log level for DANA runtime.
    
    This is the single source of truth for setting log levels in DANA.
    All components should use this function to change log levels.
    
    Args:
        level: The log level to set
    """
    DXA_LOGGER.setLevel(LEVEL_MAP[level], scope="opendxa.dana") 