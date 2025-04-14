"""
Simplified DXALogger with core logging functionality.
"""

import logging
from typing import Optional

class DXALogger:
    """Simple logger with prefix support."""
    
    # Logging level constants
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    
    def __init__(self, name: str = "opendxa", prefix: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.prefix = prefix
        self._configured = False
        self.log_data = False
        # Prevent propagation to parent loggers
        self.logger.propagate = False
    
    def configure(
        self,
        level: int = logging.WARNING,
        fmt: str = "%(asctime)s - [OpenDXA %(name)s] %(levelname)s - %(message)s",
        datefmt: str = "%H:%M:%S",
        console: bool = True,
        log_data: bool = False
    ):
        """Configure the logger with basic settings."""
        if self._configured:
            return
            
        # Remove any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        self.logger.setLevel(level)
        self.log_data = log_data
        
        if console:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        self._configured = True
    
    def setLevel(self, level: int):
        """Set the logging level."""
        self.logger.setLevel(level)
    
    def _format_message(self, message: str) -> str:
        """Add prefix to message if configured."""
        if self.prefix:
            return f"[{self.prefix}] {message}"
        return message
    
    def info(self, message: str, **context):
        """Log informational message."""
        formatted = self._format_message(message)
        if self.log_data:
            self.logger.info(formatted, extra=context)
        else:
            self.logger.info(formatted)

    def debug(self, message: str, **context):
        """Log debug message."""
        formatted = self._format_message(message)
        if self.log_data:
            self.logger.debug(formatted, extra=context)
        else:
            self.logger.debug(formatted)

    def warning(self, message: str, **context):
        """Log warning message."""
        formatted = self._format_message(message)
        if self.log_data:
            self.logger.warning(formatted, extra=context)
        else:
            self.logger.warning(formatted)

    def error(self, message: str, **context):
        """Log error message."""
        formatted = self._format_message(message)
        if self.log_data:
            self.logger.error(formatted, extra=context)
        else:
            self.logger.error(formatted)

    def getLogger(self, name: str) -> 'DXALogger':
        """Create a new logger instance with the given name."""
        return DXALogger(name, self.prefix)

# Create global logger instance
DXA_LOGGER = DXALogger("opendxa")
DXA_LOGGER.configure()