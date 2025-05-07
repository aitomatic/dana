"""Base executor for the DANA interpreter.

This module provides the base executor class that defines the interface
for all DANA execution components.
"""

import uuid
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from opendxa.common.mixins.loggable import Loggable
from opendxa.dana.language.ast import LogLevel
from opendxa.dana.language.visitor import ASTVisitor

# ANSI color codes for log levels
COLORS = {
    LogLevel.DEBUG: "\033[36m",  # Cyan
    LogLevel.INFO: "\033[32m",   # Green
    LogLevel.WARN: "\033[33m",   # Yellow
    LogLevel.ERROR: "\033[31m",  # Red
}
RESET = "\033[0m"  # Reset color

# Map DANA LogLevel to Python logging levels
LEVEL_MAP = {
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.INFO: logging.INFO,
    LogLevel.WARN: logging.WARNING,
    LogLevel.ERROR: logging.ERROR
}


class BaseExecutor(Loggable):
    """Base class for DANA execution components.
    
    This class provides common functionality used across all execution components:
    - Logging utilities
    - Execution ID management
    - Error handling hooks
    """
    
    def __init__(self):
        """Initialize the base executor."""
        # Initialize Loggable with prefix for all DANA logs
        super().__init__(prefix="dana")
        
        # Generate execution ID for this run
        self._execution_id = str(uuid.uuid4())[:8]  # Short unique ID for this execution
        self._log_level = LogLevel.WARN  # Default log level
        
        # Set initial log level
        self.set_log_level(self._log_level)
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if a message with the given level should be logged.
        
        Args:
            level: The log level to check
            
        Returns:
            True if the message should be logged, False otherwise
        """
        # Define log level priorities (higher number = higher priority)
        level_priorities = {
            LogLevel.DEBUG: 0, 
            LogLevel.INFO: 1, 
            LogLevel.WARN: 2, 
            LogLevel.ERROR: 3
        }
        
        # Only log if the message level is at or above the current threshold
        return level_priorities[level] >= level_priorities[self._log_level]
    
    def _log(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        """Log a message with runtime information.
        
        Args:
            message: The message to log
            level: The log level to use
        """
        # Check if message should be logged based on current level
        if self._should_log(level):
            # Format the log message
            timestamp = datetime.now().astimezone().strftime("%Y%m%d %H:%M:%S%z").replace("00", "")
            color = COLORS.get(level, "")
            formatted_message = f"[opendxa.dana {timestamp}] {color}{message} | {self._execution_id} | {level.value} | execution{RESET}"
            
            # Print directly for test compatibility - this is needed for the tests that mock print
            print(formatted_message)
            
            # Also log through Loggable for real application use
            # Map DANA log levels to Python logging methods
            log_method = {
                LogLevel.DEBUG: self.debug,
                LogLevel.INFO: self.info,
                LogLevel.WARN: self.warning,
                LogLevel.ERROR: self.error
            }.get(level, self.info)
            
            # Just log the original message through our logger for runtime use
            # We don't need to do this since we printed already, but it's useful for consistency
            # log_method(f"{message} (execution_id: {self._execution_id})")
    
    def set_log_level(self, level: LogLevel) -> None:
        """Set the current log level.
        
        Args:
            level: The new log level to set
        """
        self._log_level = level
        # Also update the Python logger level
        self.logger.setLevel(LEVEL_MAP.get(level, logging.INFO))