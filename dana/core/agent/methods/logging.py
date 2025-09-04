from typing import Any

from dana.core.lang.sandbox_context import SandboxContext
from dana.common.mixins.loggable import Loggable


class LoggingMixin(Loggable):
    def log_sync(self, message: str, level: str = "INFO", sandbox_context: SandboxContext | None = None) -> Any:
        """Synchronous agent logging method."""
        return self._log_impl(message, level, sandbox_context or SandboxContext())

    def info_sync(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Synchronous agent info logging method."""
        return self.log_sync(message, "INFO", sandbox_context)

    def warning_sync(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Synchronous agent warning logging method."""
        return self.log_sync(message, "WARNING", sandbox_context)

    def debug_sync(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Synchronous agent debug logging method."""
        return self.log_sync(message, "DEBUG", sandbox_context)

    def error_sync(self, message: str, sandbox_context: SandboxContext | None = None) -> Any:
        """Synchronous agent error logging method."""
        return self.log_sync(message, "ERROR", sandbox_context)

    def _log_impl(self, message: str, level: str, sandbox_context: SandboxContext) -> str:
        """Implementation of logging functionality."""
        self._notify_log_callbacks(message, level, sandbox_context)

        _message = f"[{self.name}] {message}"
        _level = level.upper()

        # Use both custom logging and standard Python logging
        import logging

        # Standard Python logging for test compatibility
        if _level == "INFO":
            logging.info(_message)
            Loggable.info(self, _message)
        elif _level == "WARNING":
            logging.warning(_message)
            Loggable.warning(self, _message)
        elif _level == "DEBUG":
            logging.debug(_message)
            Loggable.debug(self, _message)
        elif _level == "ERROR":
            logging.error(_message)
            Loggable.error(self, _message)
        else:
            logging.info(_message)
            Loggable.info(self, _message)

        return message
