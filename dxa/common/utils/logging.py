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
    """DXALogger is a simplified logging class for DXA"""
    def __init__(self):
        self.logger = logging.getLogger("dxa")
        self.logger.setLevel(logging.INFO)
        self._configured = False
        
    def configure(self, 
                  console: bool = True,
                  level: str = "info"):
        """One-click configuration with dual formatting"""
        class DualFormatter(logging.Formatter):
            """DualFormatter is a formatter that can format both LLM and timing logs"""
            def format(self, record):
                asctime = self.formatTime(record)
                
                if hasattr(record, 'prompt'):
                    # LLM format
                    return (f"{asctime} - {record.levelname} - {record.msg} | "
                            f"Details: {record.prompt} | Response: {record.response} | "
                            f"Model: {getattr(record, 'model', 'N/A')}")
                elif hasattr(record, 'operation'):
                    # Timing format
                    return (f"{asctime} - {record.levelname} - {record.msg}\n"
                            f"operation: {record.operation}\n"
                            f"duration: {record.duration}\n"
                            f"{', '.join(f'{k}: {v}' for k, v in record.__dict__.items() 
                                         if k not in ['operation', 'duration'])}")
                # Basic format
                return f"{asctime} - {record.levelname} - {record.msg}"
        
        formatter = DualFormatter(
            fmt='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        if console:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.setLevel(getattr(logging, level.upper()))
        self._configured = True
    
    def debug(self, message: str, **context):
        """Log debug message with optional context"""
        self.logger.debug(message, extra={'context': context})

    def info(self, message: str, **context):
        """Log informational message with optional context"""
        self.logger.info(message, extra={'context': context})

    def warning(self, message: str, **context):
        """Log warning with optional context"""
        self.logger.warning(message, extra={'context': context})

    def error(self, message: str, **context):
        """Log error with optional context"""
        self.logger.error(message, extra={'context': context})

    def log_llm(self,
                prompt: str,
                response: str,
                model: str,
                tokens: Optional[int] = None):
        """Log LLM interaction"""
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
        """Log LLM-specific error"""
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
        duration = perf_counter() - self.start_time
        # Log directly using configured formatter
        self.logger.info(
            f"Operation '{self.name}' completed in {duration:.2f}s",
            **self.metadata
        )
