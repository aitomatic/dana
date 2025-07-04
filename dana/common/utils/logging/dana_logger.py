"""
Dana Logger with core logging functionality.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Literal, TypeVar, overload

T = TypeVar("T")
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds color to log levels."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
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


class DanaLogger:
    """Simple logger with prefix support and enhanced functionality."""

    # Logging level constants
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    def __init__(self, name: str = "dana", prefix: str | None = None) -> None:
        """Initialize the logger.

        Args:
            name: The logger name
            prefix: Optional prefix for log messages
        """
        self.logger = logging.getLogger(name)
        self.prefix = prefix
        self._configured = False
        # Allow propagation to parent loggers
        self.logger.propagate = True

    def configure(
        self,
        level: int = logging.WARNING,
        fmt: str = "%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
        datefmt: str = "%H:%M:%S",
        console: bool = True,
        **kwargs: Any,  # Accept but ignore extra args for backward compatibility
    ) -> None:
        """Configure the logger with basic settings.

        Only affects Dana loggers to avoid interfering with third-party libraries.
        """
        if self._configured:
            return

        # Configure only the Dana root logger, not the system root logger
        dana_root = logging.getLogger("dana")
        dana_root.setLevel(level)

        # Add our handler to the Dana root logger only if console logging is enabled
        if console:
            # Remove any existing handlers on the Dana logger
            for handler in dana_root.handlers[:]:
                dana_root.removeHandler(handler)

            handler = logging.StreamHandler()
            formatter = ColoredFormatter(fmt=fmt, datefmt=datefmt)
            handler.setFormatter(formatter)
            dana_root.addHandler(handler)
            # Prevent propagation to avoid duplicate messages
            dana_root.propagate = False

        # Configure this logger and only existing Dana loggers
        self.logger.setLevel(level)
        for logger_name in logging.Logger.manager.loggerDict:
            if logger_name.startswith("dana"):
                logger = logging.getLogger(logger_name)
                if isinstance(logger, logging.Logger):
                    logger.setLevel(level)

        self._configured = True

    def _configure_third_party_logging(self) -> None:
        """Configure third-party library logging to reduce noise.

        This suppresses verbose logging from libraries commonly used in Dana
        that produce excessive output at INFO level.
        """
        # HTTP client libraries
        for logger_name in ["httpx", "httpcore", "h11", "openai", "urllib3"]:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

        # Suppress httpx._client specifically as it's particularly verbose
        logging.getLogger("httpx._client").setLevel(logging.WARNING)

        # Other commonly noisy libraries
        for logger_name in ["asyncio", "filelock"]:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

    def setLevel(self, level: int, scope: str | None = "dana") -> None:
        """Set the logging level with configurable scope.

        By default, sets level for all Dana components. This ensures that
        DANA_LOGGER.setLevel(DEBUG) affects the entire Dana system.

        Args:
            level: The logging level to set (e.g., logging.DEBUG, logging.INFO)
            scope: Optional scope parameter:
                  - "dana" (default): Set level for all Dana components
                  - "*": Set level for all loggers system-wide
                  - None: Set level only for this logger instance
                  - "dana.agent": Set level for specific Dana subsystem
        """
        if scope is None:
            # Set level only for this logger instance
            self.logger.setLevel(level)
        elif scope == "*":
            # Set level for all loggers system-wide
            logging.getLogger().setLevel(level)
            for logger_name in logging.Logger.manager.loggerDict:
                logger = logging.getLogger(logger_name)
                if isinstance(logger, logging.Logger):
                    logger.setLevel(level)
        else:
            # Set level for all loggers starting with the given scope
            scope_logger = logging.getLogger(scope)
            scope_logger.setLevel(level)

            # Update existing loggers in the scope (for future inheritance)
            self._update_scope_loggers(level, scope)

    def _update_scope_loggers(self, level: int, scope: str) -> None:
        """Update all existing loggers within the specified scope.

        This ensures that existing loggers that may have been configured
        independently still respect the new level setting.
        """
        for logger_name in logging.Logger.manager.loggerDict:
            if logger_name.startswith(f"{scope}.") or logger_name == scope:
                logger = logging.getLogger(logger_name)
                if isinstance(logger, logging.Logger):
                    logger.setLevel(level)

    def _format_message(self, message: str) -> str:
        """Add prefix to message if configured."""
        if self.prefix:
            return f"[{self.prefix}] {message}"
        return message

    def _log(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        """Internal method to handle all logging."""
        # Skip expensive formatting if logging is disabled
        if not self.logger.isEnabledFor(level):
            return

        formatted = self._format_message(message)
        self.logger.log(level, formatted, *args, **kwargs)

    @overload
    def log(self, level: int, message: str, *args: Any, **kwargs: Any) -> None: ...

    @overload
    def log(self, level: LogLevel, message: str, *args: Any, **kwargs: Any) -> None: ...

    def log(self, level: int | LogLevel, message: str, *args: Any, **kwargs: Any) -> None:
        """Log message with specified level."""
        if isinstance(level, str):
            level = getattr(logging, level)
        elif hasattr(level, "value"):  # Handle LogLevel enum
            level = level.value

        # Ensure level is an int
        if not isinstance(level, int):
            raise ValueError(f"Invalid log level: {level}")

        self._log(level, message, *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log informational message."""
        self._log(logging.INFO, message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, *args, **kwargs)

    def getLogger(self, name_or_obj: str | Any, prefix: str | None = None) -> "DanaLogger":
        """Create a new logger instance.

        Args:
            name_or_obj: Either a string name for the logger, or an object to create a logger for.
                        If an object is provided, the logger name will be based on the object's
                        class module and name.
            prefix: Optional prefix for log messages

        Returns:
            DanaLogger instance
        """
        if isinstance(name_or_obj, str):
            return DanaLogger(name_or_obj, prefix or self.prefix)
        else:
            return DanaLogger.getLoggerForClass(name_or_obj.__class__, prefix or self.prefix)

    @classmethod
    @lru_cache(maxsize=128)  # Increased cache size for better performance
    def getLoggerForClass(cls, for_class: type[Any], prefix: str | None = None) -> "DanaLogger":
        """Get a logger for a class.

        Args:
            for_class: The class to get the logger for.
            prefix: Optional prefix for log messages

        Returns:
            DanaLogger instance
        """
        return cls(f"{for_class.__module__}.{for_class.__name__}", prefix)

    @contextmanager
    def with_level(self, level: int) -> Generator[None, None, None]:
        """Context manager to temporarily change log level.

        Example:
            >>> with DANA_LOGGER.with_level(logging.DEBUG):
            ...     DANA_LOGGER.debug("This will be logged")
            >>> DANA_LOGGER.debug("This might not be logged")
        """
        original_level = self.logger.level
        self.logger.setLevel(level)
        try:
            yield
        finally:
            self.logger.setLevel(original_level)

    @contextmanager
    def with_prefix(self, prefix: str) -> Generator["DanaLogger", None, None]:
        """Context manager to temporarily use a different prefix.

        Example:
            >>> with DANA_LOGGER.with_prefix("PROCESSING") as logger:
            ...     logger.info("Starting processing")
        """
        temp_logger = DanaLogger(self.logger.name, prefix)
        temp_logger.logger = self.logger  # Share the same underlying logger
        temp_logger._configured = self._configured
        yield temp_logger

    def lazy(self, level: int, message_func: Any, *args: Any, **kwargs: Any) -> None:
        """Log with lazy evaluation of expensive message generation.

        Example:
            >>> DANA_LOGGER.lazy(
            ...     logging.DEBUG,
            ...     lambda: f"Expensive computation: {expensive_function()}"
            ... )
        """
        if self.logger.isEnabledFor(level):
            message = message_func() if callable(message_func) else str(message_func)
            self._log(level, message, *args, **kwargs)

    # Backward compatibility - remove eventually
    def setBasicConfig(self, *args: Any, **kwargs: Any) -> None:
        """Configure the logging system with basic settings.

        Deprecated: Use configure() instead.
        """
        logging.basicConfig(*args, **kwargs)


# Create global logger instances
DANA_LOGGER = DanaLogger("dana")  # Main Dana logger

# Configure the logger
DANA_LOGGER.configure()

# Configure third-party logging globally
DANA_LOGGER._configure_third_party_logging()

# For backward compatibility, also create DanaLogger as alias
# Legacy alias for backward compatibility
DanaLoggerSingleton = DANA_LOGGER
