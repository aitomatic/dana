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
    def __init__(self, log_data: bool = False):
        self.logger = logging.getLogger("dxa")
        self._configured = False
        self.log_data = log_data  # Control data visibility
        
        # Default configuration
        if not self.logger.handlers:
            self._setup_basic_config()
    
    def _setup_basic_config(self):
        """Set up minimal console logging by default"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def configure(self, 
                  console: bool = True,
                  level: str = "info",
                  log_data: bool = False):
        """One-click configuration with dual formatting"""
        self.log_data = log_data
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        class DualFormatter(logging.Formatter):
            """DualFormatter is a formatter that can format both LLM and timing logs"""
            def format(self, record):
                original = super().format(record)
                
                # Get the logging context
                context = getattr(record, 'context', {})
                
                # Only show data for execution-related logs
                data_keys = {
                    'result_data'  # Only log final output data
                }
                if not data_keys.intersection(context.keys()):
                    return original
                
                # Format output data and metadata
                lines = []
                if 'result_data' in context:
                    lines.append(f"output_data: {context['result_data']}")
                
                param_str = "\n    ".join(lines)
                return f"{original}\n    {param_str}"
        
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

    def log(self, level: str, message: str, **context):
        """Generic logging method for any level"""
        level_upper = level.upper()
        self.logger.log(
            getattr(logging, level_upper),
            message,
            extra={'context': context}
        )

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

# Create preconfigured instance
dxa_logger = DXALogger()
