"""Loggable abstract base class for standardized logging across the codebase."""

import logging
from typing import Any

from dana.common.utils.logging import DANA_LOGGER


class Loggable:
    """Base class for objects that need logging capabilities.

    Classes inheriting from Loggable automatically get a configured logger
    using a standardized naming convention. This eliminates the need for
    repetitive logger initialization code across the codebase.

    Usage:
        class MyClass(Loggable):
            def __init__(self):
                super().__init__()  # That's it!

            def my_method(self):
                self.info("This is a log message")  # Convenience method
                # or
                self.logger.info("This is a log message")  # Direct access

            def change_level(self):
                self.logger.setLevel(logging.DEBUG)  # Configure through logger
    """

    def __init__(self, logger_name: str | None = None, prefix: str | None = None, log_data: bool = False, level: int | None = None):
        """Initialize with a standardized logger.

        Args:
            logger_name: Optional custom logger name. If not provided,
                         automatically determined from class hierarchy.
            prefix: Optional prefix for log messages.
            log_data: Whether to log data payloads (default: False).
            level: Optional logging level. If not provided, inherits from parent.
        """
        # Initialize logger using either custom name or object's class module and name
        self._logger = self.__instantiate_logger(logger_name, prefix, log_data, level)

    def __instantiate_logger(
        self, logger_name: str | None = None, prefix: str | None = None, log_data: bool = False, level: int | None = None
    ):
        """Initialize a logger instance.

        Args:
            logger_name: Optional custom logger name
            prefix: Optional prefix for log messages
            log_data: Whether to log data payloads (deprecated, ignored)
            level: Optional logging level. If not provided, inherits from hierarchy.

        Returns:
            The configured logger instance
        """
        self._logger = DANA_LOGGER.getLogger(logger_name or self, prefix)

        # Only configure if the global DANA_LOGGER system hasn't been configured yet
        # This prevents individual Loggable instances from overriding global settings
        if not DANA_LOGGER._configured:
            self._logger.configure(
                console=True,
                level=level if level is not None else logging.WARNING,
                fmt="%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
                datefmt="%H:%M:%S",
            )
        elif level is not None:
            # If explicitly provided level, set it even if already configured
            self._logger.setLevel(level)

        return self._logger

    @property
    def logger(self):
        """Get the logger for this instance"""
        if not hasattr(self, "_logger"):
            self._logger = self.__instantiate_logger()
        return self._logger

    def debug(self, message: str, *args, **context) -> None:
        """Log a debug message."""
        self.logger.debug(message, *args, **context)

    def info(self, message: str, *args, **context) -> None:
        """Log an info message."""
        self.logger.info(message, *args, **context)

    def warning(self, message: str, *args, **context) -> None:
        """Log a warning message."""
        self.logger.warning(message, *args, **context)

    def error(self, message: str, *args, **context) -> None:
        """Log an error message."""
        self.logger.error(message, *args, **context)

    @classmethod
    def log_debug(cls, message: str, *args, **context) -> None:
        """Log a debug message."""
        cls.get_class_logger().debug(message, *args, **context)

    @classmethod
    def log_info(cls, message: str, *args, **context) -> None:
        """Log an info message."""
        cls.get_class_logger().info(message, *args, **context)

    @classmethod
    def log_warning(cls, message: str, *args, **context) -> None:
        """Log a warning message."""
        cls.get_class_logger().warning(message, *args, **context)

    @classmethod
    def log_error(cls, message: str, *args, **context) -> None:
        """Log an error message."""
        cls.get_class_logger().error(message, *args, **context)

    @classmethod
    def get_class_logger(cls) -> Any:
        """Get a logger for the class itself."""
        return DANA_LOGGER.getLoggerForClass(cls)
