"""
Simplified DXALogger with core logging functionality.
"""

import logging
from typing import Optional, Any, Union

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
    
    def setBasicConfig(self, *args, **kwargs):
        """Configure the logging system with basic settings."""
        logging.basicConfig(*args, **kwargs)
        
    def setLevel(self, level: int, scope: Optional[str] = "*"):
        """Set the logging level with configurable scope.
        
        Args:
            level: The logging level to set (e.g., logging.DEBUG, logging.INFO)
            scope: Optional scope parameter:
                  - "*" (default): Set level for all loggers created by this DXA_LOGGER instance
                  - None: Set level only for this logger instance
                  - "opendxa": Set level for all loggers starting with "opendxa"
                  - "opendxa.agent": Set level for all loggers starting with "opendxa.agent"
        """
        if scope is None:
            # Set level only for this logger instance
            self.logger.setLevel(level)
        elif scope == "*":
            # Set level for all loggers created by this DXA_LOGGER instance
            for logger_name in logging.Logger.manager.loggerDict:
                if isinstance(logging.getLogger(logger_name), logging.Logger):
                    logging.getLogger(logger_name).setLevel(level)
        else:
            # Set level for all loggers starting with the given scope
            for logger_name in logging.Logger.manager.loggerDict:
                if logger_name.startswith(scope):
                    logging.getLogger(logger_name).setLevel(level)
    
    def _format_message(self, message: str) -> str:
        """Add prefix to message if configured."""
        if self.prefix:
            return f"[{self.prefix}] {message}"
        return message
    
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

    def getLogger(self, name_or_obj: Union[str, Any]) -> 'DXALogger':
        """Create a new logger instance.
        
        Args:
            name_or_obj: Either a string name for the logger, or an object to create a logger for.
                        If an object is provided, the logger name will be based on the object's
                        class module and name.
                        
        Returns:
            DXALogger instance
        """
        if isinstance(name_or_obj, str):
            return DXALogger(name_or_obj, self.prefix)
        else:
            cls = name_or_obj.__class__
            return DXALogger(f"{cls.__module__}.{cls.__name__}", self.prefix)

# Create global logger instance
DXA_LOGGER = DXALogger("opendxa")
DXA_LOGGER.configure()