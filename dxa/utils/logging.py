"""Logging configuration for the MUA system."""

import logging
from typing import Optional, List
import json

class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON-formatted logs."""
    
    def __init__(self, include_performance: bool = True):
        super().__init__()
        self.include_performance = include_performance

    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage()
        }
        
        if self.include_performance and hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
            
        # Include any extra fields from the record
        if record.__dict__.get('extra'):
            log_data.update(record.__dict__['extra'])
            
        return json.dumps(log_data)

def configure_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
    json_logs: bool = False,
    include_performance: bool = True,
    handlers: Optional[List[logging.Handler]] = None
) -> None:
    """Configure logging for the MUA system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for logs
        log_file: Path to log file (if None, logs to console only)
        json_logs: If True, output logs in JSON format
        include_performance: If True, include performance metrics in logs
        handlers: Optional list of custom handlers
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    if handlers:
        for handler in handlers:
            root_logger.addHandler(handler)
    else:
        # Create default handlers
        if json_logs:
            formatter = JSONFormatter(include_performance=include_performance)
        else:
            if not format_string:
                base_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                if include_performance:
                    base_format += ' - Duration: %(duration_ms)sms'
                format_string = base_format
            formatter = logging.Formatter(format_string)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

    # Log configuration details
    logger = logging.getLogger(__name__)
    logger.debug(
        "Logging configured",
        extra={
            "level": level,
            "json_logs": json_logs,
            "log_file": log_file,
            "include_performance": include_performance
        }
    )
