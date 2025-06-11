"""
Simplified DXALogger with core logging functionality.
"""

import logging
from functools import lru_cache
from typing import Any, cast


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds color to log levels."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        # Get the original format
        formatted = super().format(record)

        # Add color to the level name and everything after it
        levelname = record.levelname
        if levelname in self.COLORS:
            # Find the position of the level name in the formatted string
            level_pos = formatted.find(levelname)
            if level_pos != -1:
                # Add color before the level name and keep it until the end
                formatted = formatted[:level_pos] + self.COLORS[levelname] + formatted[level_pos:] + self.COLORS["RESET"]

        return formatted


class DXALogger:
    """Simple logger with prefix support."""

    # Logging level constants
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR

    def __init__(self, name: str = "opendxa", prefix: str | None = None):
        """Initialize the logger.

        Args:
            name: The logger name
            prefix: Optional prefix for log messages
        """
        self.logger = logging.getLogger(name)
        self.prefix = prefix
        self._configured = False
        self.log_data = False
        # Allow propagation to parent loggers
        self.logger.propagate = True

    def configure(
        self,
        level: int = logging.WARNING,
        fmt: str = "%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
        datefmt: str = "%H:%M:%S",
        console: bool = True,
        log_data: bool = False,
    ):
        """Configure the logger with basic settings."""
        if self._configured:
            return

        # Configure the root logger
        root = logging.getLogger()
        root.setLevel(level)

        # Remove any existing handlers
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        # Add our handler to the root logger
        if console:
            handler = logging.StreamHandler()
            formatter = ColoredFormatter(fmt=fmt, datefmt=datefmt)
            handler.setFormatter(formatter)
            root.addHandler(handler)

        # Configure this logger and all existing loggers
        self.logger.setLevel(level)
        for logger_name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            if isinstance(logger, logging.Logger):
                logger.setLevel(level)

        self.log_data = log_data
        self._configured = True

    def setBasicConfig(self, *args, **kwargs):
        """Configure the logging system with basic settings."""
        logging.basicConfig(*args, **kwargs)

    def setLevel(self, level: int, scope: str | None = "*"):
        """Set the logging level with configurable scope.

        Args:
            level: The logging level to set (e.g., logging.DEBUG, logging.INFO)
            scope: Optional scope parameter:
                  - "*" (default): Set level for all loggers
                  - None: Set level only for this logger instance
                  - "opendxa": Set level for all loggers starting with "opendxa"
                  - "opendxa.agent": Set level for all loggers starting with "opendxa.agent"
        """
        if scope is None:
            # Set level only for this logger instance
            self.logger.setLevel(level)
        elif scope == "*":
            # Set level for all loggers
            logging.getLogger().setLevel(level)
            for logger_name in logging.Logger.manager.loggerDict:
                logger = logging.getLogger(logger_name)
                if isinstance(logger, logging.Logger):
                    logger.setLevel(level)
        else:
            # Set level for all loggers starting with the given scope
            scope_logger = logging.getLogger(scope)
            scope_logger.setLevel(level)
            # Also set all child loggers
            for logger_name in logging.Logger.manager.loggerDict:
                if logger_name.startswith(scope + "."):
                    logger = logging.getLogger(logger_name)
                    if isinstance(logger, logging.Logger):
                        logger.setLevel(level)

    def _format_message(self, message: str) -> str:
        """Add prefix to message if configured."""
        if self.prefix:
            return f"[{self.prefix}] {message}"
        return message

    def log(self, level: int | str, message: str, *args, **context):
        """Log message with specified level."""
        formatted = self._format_message(message)

        if isinstance(level, str):
            level = cast(int, getattr(logging, level))

        if self.log_data:
            self.logger.log(level, formatted, *args, extra=context)
        else:
            self.logger.log(level, formatted, *args)

    def info(self, message: str, *args, **context):
        """Log informational message."""
        formatted = self._format_message(message)
        if self.log_data:
            self.logger.info(formatted, *args, extra=context)
        else:
            self.logger.info(formatted, *args)

    def debug(self, message: str, *args, **context):
        """Log debug message."""
        formatted = self._format_message(message)
        if self.log_data:
            self.logger.debug(formatted, *args, extra=context)
        else:
            self.logger.debug(formatted, *args)

    def warning(self, message: str, *args, **context):
        """Log warning message."""
        formatted = self._format_message(message)
        if self.log_data:
            self.logger.warning(formatted, *args, extra=context)
        else:
            self.logger.warning(formatted, *args)

    def error(self, message: str, *args, **context):
        """Log error message."""
        formatted = self._format_message(message)
        if self.log_data:
            self.logger.error(formatted, *args, extra=context)
        else:
            self.logger.error(formatted, *args)

    def getLogger(self, name_or_obj: str | Any, prefix: str | None = None) -> "DXALogger":
        """Create a new logger instance.

        Args:
            name_or_obj: Either a string name for the logger, or an object to create a logger for.
                        If an object is provided, the logger name will be based on the object's
                        class module and name.

        Returns:
            DXALogger instance
        """
        if isinstance(name_or_obj, str):
            return DXALogger(name_or_obj, prefix or self.prefix)
        else:
            return DXALogger.getLoggerForClass(name_or_obj.__class__, prefix or self.prefix)

    @classmethod
    @lru_cache(maxsize=32)
    def getLoggerForClass(cls, for_class: Any, prefix: str | None = None) -> "DXALogger":
        """Get a logger for a class.

        Args:
            for_class: The class to get the logger for.

        Returns:
            DXALogger instance
        """
        return DXALogger(f"{for_class.__module__}.{for_class.__name__}", prefix)


# Create global logger instance
DXA_LOGGER = DXALogger("opendxa")
DXA_LOGGER.configure()
