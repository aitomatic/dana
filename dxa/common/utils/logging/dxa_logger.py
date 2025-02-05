"""
Simplified DXALogger with three core methods:
1. log() - Basic logging
2. track() - Timed operations
3. error() - Error handling
"""

from time import perf_counter
from typing import Optional
import logging

class DXALogger:
    """DXALogger requires explicit configuration. Usage:
    
    logger = DXALogger().configure()
    """

    # Convenience constants for logging levels
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR

    @classmethod
    def getLogger(cls, name: str = "dxa") -> 'DXALogger':
        """Convenience method to get a new logger instance"""
        return dxa_logging.getLogger(name)

    @classmethod
    def basicConfig(cls, **kwargs):
        """Convenience method to configure the logger"""
        dxa_logging.basicConfig(**kwargs)

    def __init__(self, name: str = "dxa", prefix: Optional[str] = None, log_data: bool = False):
        self.logger = logging.getLogger(name)
        self.prefix = prefix  # Store prefix at logger level
        # Clear existing handlers to prevent inheritance
        self.logger.handlers = []
        self._configured = False
        self.log_data = log_data  # Control data visibility
        self._name = name  # Store name internally
        self.logger.propagate = False  # Prevent duplicate logging
    
    def configure(self, 
                  console: bool = True,
                  level: int = logging.INFO,
                  log_data: bool = False,
                  fmt: str = "%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
                  datefmt: str = "%Y-%m-%d %H:%M:%S"):
        """ Configure the logger """
        self.logger.setLevel(level)
        self.log_data = log_data
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        formatter = logging.Formatter(
            fmt=fmt,
            datefmt=datefmt,
            style='%'  # Explicitly set printf-style
        )
        
        if console:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self._configured = True
    
    def _format_message(self, message: str, context: dict) -> str:
        """Combine prefix from context or instance"""
        prefix = context.get('prefix', self.prefix)
        return f"[{prefix}] {message}" if prefix else message

    def info(self, message: str, *args, **context):
        """Log informational message with optional context"""
        formatted = self._format_message(message, context)
        self.logger.info(formatted, *args, **context)

    def debug(self, message: str, *args, **context):
        """Log debug message with optional context"""
        formatted = self._format_message(message, context)
        self.logger.debug(formatted, *args, **context)

    def warning(self, message: str, *args, **context):
        """Log warning message with optional context"""
        formatted = self._format_message(message, context)
        self.logger.warning(formatted, *args, **context)

    def error(self, message: str, *args, **context):
        """Log error message with optional context"""
        formatted = self._format_message(message, context)
        self.logger.error(formatted, *args, **context)

    def log_llm(self,
                prompt: str,
                response: str,
                model: str,
                tokens: Optional[int] = None):
        """Specialized method for LLM interactions"""
        entry = {
            'prompt': prompt,
            'response': response,
            'model': model,
            'tokens': tokens
        }
        self.logger.info("LLM Interaction", extra=entry)

    def log_llm_error(self,
                      message: str,
                      model: str,
                      error_type: str = "api_error",
                      **context):
        """Specialized error logging for LLM operations"""
        entry = {
            'error_type': error_type,
            'model': model,
            'error_details': message,
            'context': context
        }
        self.logger.error("LLM Error: %s", error_type, extra=entry)
    
    def track(self, operation: str):
        """Timed operations context manager"""
        return TimedOperation(self, operation)

    def log(self, level: str, message: str, **context):
        """Generic logging method for any level"""
        level_upper = level.upper()
        self.logger.log(
            getattr(logging, level_upper),
            message,
            extra={'context': context}
        )

    def getChild(self, suffix: str) -> 'DXALogger':
        """Create isolated child logger"""
        child = DXALogger(f"{self._name}.{suffix}", self.prefix)
        child.logger.propagate = False  # Different from standard behavior
        return child

    def get_log_level(self) -> str:
        """Get current logging level."""
        return logging.getLevelName(self.logger.level)

class TimedOperation:
    """Timed operations context manager"""
    def __init__(self, logger: DXALogger, name: str):
        self.logger = logger
        self.name = name
        self.start_time = None
        self.metadata = {}
    
    def __enter__(self):
        self.start_time = perf_counter()
        return self
    
    def add_meta(self, **kwargs):
        """Add operation metadata"""
        self.metadata.update(kwargs)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Ensure start_time is initialized before calculation
        assert self.start_time is not None, "Operation was not started"
        duration = perf_counter() - self.start_time
        # Log directly using configured formatter
        self.logger.info(
            f"Operation '{self.name}' completed in {duration:.2f}s",
            **self.metadata
        )


class dxa_logging:
    """DXA Logging"""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR

    _STANDARD_CONFIG = {
        "console": True,
        "level": logging.WARNING,
        "log_data": False,
        "fmt": "%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
        "datefmt": "%H:%M:%S"
    }

    """DXA Logging"""
    @staticmethod
    def getLogger(name: str = "dxa") -> DXALogger:
        """Module-level getter following standard logging interface"""
        new_logger = DXALogger(name)
        new_logger.configure(**dxa_logging._STANDARD_CONFIG)
        return new_logger

    @staticmethod
    def basicConfig(**kwargs):
        """Class-level configuration following standard logging pattern"""
        # Replace existing configuration entries with kwargs
        for key, value in kwargs.items():
            dxa_logging._STANDARD_CONFIG[key] = value
        
        # also updatehe dxa_logger config
        DXA_LOGGER.configure(**dxa_logging._STANDARD_CONFIG)

DXA_LOGGER = dxa_logging.getLogger("DXA")