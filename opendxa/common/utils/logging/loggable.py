"""Loggable abstract base class for standardized logging across the codebase."""

from abc import ABC
import logging
from typing import Optional, Any

from .dxa_logger import DXA_LOGGER


class Loggable(ABC):
    """Base class for objects that need logging capabilities.
    
    Classes inheriting from Loggable automatically get a configured logger
    using a standardized naming convention. This eliminates the need for
    repetitive logger initialization code across the codebase.
    
    Usage:
        class MyClass(Loggable):
            def __init__(self):
                super().__init__()  # That's it!
                
            def my_method(self):
                self.logger.info("This is a log message")
    
    The logger is automatically configured with the appropriate name based on:
    1. The module hierarchy (e.g., dxa.execution.planning)
    2. The class name
    
    Advanced usage allows for custom logger names and prefixes if needed.
    """
    
    def __init__(self, 
                 logger_name: Optional[str] = None, 
                 prefix: Optional[str] = None,
                 log_data: bool = False,
                 level: int = logging.INFO):
        """Initialize with a standardized logger.
        
        Args:
            logger_name: Optional custom logger name. If not provided, 
                         automatically determined from class hierarchy.
            prefix: Optional prefix for log messages.
            log_data: Whether to log data payloads (default: False).
            level: Logging level (default: INFO).
        """
        # Get the class that's actually being instantiated (not Loggable)
        cls = self.__class__
        
        # If no custom logger name, generate one based on module path and class name
        if logger_name is None:
            # Get module name, handling nested classes
            module = cls.__module__
            
            # If not a built-in module, create hierarchical name
            if module != "__main__":
                # For execution layer classes, extract the layer name if available
                layer = getattr(self, "layer", None)
                if layer and hasattr(self, "layer"):
                    logger_name = f"opendxa.execution.{layer}"
                else:
                    # Create name from module path, ensuring dxa prefix
                    if module.startswith("opendxa."):
                        logger_name = f"{module}.{cls.__name__}"
                    else:
                        logger_name = f"opendxa.{module}.{cls.__name__}"
            else:
                logger_name = cls.__name__
        
        # Initialize logger using DXA_LOGGER
        self.logger = DXA_LOGGER.getLogger(logger_name)
        
        # Ensure the logger is configured
        if not self.logger._configured:
            # Configure the logger with a console handler
            self.logger.configure(
                console=True,
                level=level,
                log_data=log_data,
                fmt="%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
                datefmt="%H:%M:%S"
            )
        
        # Set prefix if provided
        if prefix:
            self.logger.prefix = prefix
            
        # Configure data logging
        self.logger.log_data = log_data
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log a debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log an info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log a warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log an error message."""
        self.logger.error(message, *args, **kwargs)
    
    @classmethod
    def get_class_logger(cls) -> Any:
        """Get a logger for class-level (static) methods."""
        # Create name from module path, ensuring dxa prefix
        module = cls.__module__
        if module.startswith("opendxa."):
            logger_name = f"{module}.{cls.__name__}"
        else:
            logger_name = f"opendxa.{module}.{cls.__name__}"
            
        logger = DXA_LOGGER.getLogger(logger_name)
        
        # Ensure the logger is configured
        if not logger._configured:  # pylint: disable=protected-access
            # Configure the logger with a console handler
            logger.configure(
                console=True,
                level=logging.INFO,
                fmt="%(asctime)s - [%(name)s] %(levelname)s - %(message)s",
                datefmt="%H:%M:%S"
            )
            
        return logger 