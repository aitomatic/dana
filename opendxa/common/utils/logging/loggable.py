"""Loggable abstract base class for standardized logging across the codebase."""

from typing import Optional
import logging

from .dxa_logger import DXA_LOGGER


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
    
    def __init__(self, 
                 logger_name: Optional[str] = None, 
                 prefix: Optional[str] = None,
                 log_data: bool = False,
                 level: Optional[int] = None):
        """Initialize with a standardized logger.
        
        Args:
            logger_name: Optional custom logger name. If not provided, 
                         automatically determined from class hierarchy.
            prefix: Optional prefix for log messages.
            log_data: Whether to log data payloads (default: False).
            level: Optional logging level. If not provided, inherits from parent.
        """
        # Get the class that's actually being instantiated (not Loggable)
        cls = self.__class__
        
        # If no custom logger name, use just the class name
        if logger_name is None:
            logger_name = cls.__name__
        
        # Initialize logger using DXA_LOGGER
        self.logger = DXA_LOGGER.getLogger(logger_name)
        
        # Configure the logger
        self.logger.configure(
            console=True,
            level=level or logging.WARNING,
            log_data=log_data,
            fmt="%(asctime)s - [OpenDXA %(name)s] %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
        
        # Set prefix if provided
        if prefix:
            self.logger.prefix = prefix
    
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
    def get_class_logger(cls) -> 'Loggable':
        """Get a logger for the class itself."""
        return Loggable(cls.__name__) 