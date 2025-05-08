"""Loggable abstract base class for standardized logging across the codebase."""

import logging
from typing import Optional

from opendxa.common.utils.logging.dxa_logger import DXA_LOGGER


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

    def __init__(
        self, logger_name: Optional[str] = None, prefix: Optional[str] = None, log_data: bool = False, level: Optional[int] = None
    ):
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
        self, logger_name: Optional[str] = None, prefix: Optional[str] = None, log_data: bool = False, level: Optional[int] = None
    ):
        self._logger = DXA_LOGGER.getLogger(logger_name or self, prefix)
        self._logger.configure(
            console=True,
            level=level or logging.WARNING,
            log_data=log_data,
            fmt="%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
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
    def get_class_logger(cls) -> "Loggable":
        """Get a logger for the class itself."""
        return DXA_LOGGER.getLoggerForClass(cls)
