"""Logging for DXA.

A unified logging system that provides:
- File and console logging with rotation
- Structured logging with JSON support
- Thread-safe LLM interaction tracking
- Token usage and response time metrics
- Built-in analysis and visualization tools
- Automatic log sanitization

Basic Usage:
    # Initialize logger
    logger = DXALogger(log_dir="logs")
    
    # Log an LLM interaction
    logger.log_llm_interaction({
        "interaction_type": "completion",
        "content": "User prompt",
        "response": {"content": "AI response", "usage": {"total_tokens": 150}},
        "success": True
    })

    # Simple completion logging
    logger.log_completion(
        prompt="What is 2+2?",
        response="4",
        tokens=10
    )

    # Error logging
    logger.log_error(
        error_type="validation",
        message="Invalid input format"
    )

    # Timing interactions
    with logger.log_interaction_timing("completion"):
        response = llm.complete(prompt)

Advanced Features:
    # Get analytics
    analyzer = logger.get_analyzer()
    stats = analyzer.get_interaction_stats()

    # Create visualizations
    visualizer = logger.get_visualizer()
    visualizer.create_dashboard("dashboard/")
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict
from datetime import datetime
from threading import Lock
from collections import Counter
import time
import re
from contextlib import contextmanager
import structlog
from .log_analysis import LLMInteractionAnalyzer
from .log_viz import LLMInteractionVisualizer

__all__ = ['DXALogger']  # Export the class

class DXALogger:
    """Unified logging for DXA system"""
    
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        log_dir: Optional[str] = None,
        log_level: str = "INFO",
        max_history: int = 1000,
        **kwargs
    ):
        self._lock = Lock()
        self.log_dir = log_dir
        self.max_history = max_history
        self.llm_history = []
        self.metrics = {
            'total_tokens': 0,
            'total_calls': Counter(),
            'errors': Counter(),
            'response_times': []
        }
        self.configure_logging(log_dir, log_level, **kwargs)
        
    def configure_logging(self, log_dir: Optional[str], log_level: str, **kwargs):
        """Configure system-wide logging"""
        # Configure structured logging
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ],
            logger_factory=structlog.PrintLoggerFactory(),
        )
        self.structured_logger = structlog.get_logger()
        
        # Create root logger
        self.logger = logging.getLogger('dxa')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatters
        json_format = kwargs.get('json_format', False)
        if json_format:
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "logger": "%(name)s", '
                '"level": "%(levelname)s", "message": "%(message)s", '
                '"llm_name": "%(llm_name)s", "model": "%(model)s", '
                '"interaction_type": "%(interaction_type)s"}'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s - '
                'LLM: %(llm_name)s - Model: %(model)s - Type: %(interaction_type)s'
            )
        
        # Set up file logging if directory specified
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
            # Main log file - rotate by size
            main_handler = RotatingFileHandler(
                os.path.join(log_dir, 'dxa.log'),
                maxBytes=kwargs.get('max_bytes', 10_000_000),
                backupCount=kwargs.get('backup_count', 5)
            )
            main_handler.setFormatter(formatter)
            self.logger.addHandler(main_handler)
        
            # LLM-specific log file
            llm_handler = RotatingFileHandler(
                os.path.join(log_dir, 'llm_interactions.log'),
                maxBytes=kwargs.get('max_bytes', 10_000_000),
                backupCount=kwargs.get('backup_count', 5)
            )
            llm_handler.setFormatter(formatter)
            
            # Only capture LLM logs
            llm_handler.addFilter(lambda record: record.name.startswith('dxa.llm'))
            self.logger.addHandler(llm_handler)
        
        # Set up console logging if requested
        console_output = kwargs.get('console_output', True)
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def _sanitize_log_data(self, data: Dict) -> Dict:
        """Sanitize sensitive information from log data"""
        sensitive_patterns = [
            (r'api[_-]key["\s]*[:=]\s*["\']?\w+["\']?', '[REDACTED]'),
            (r'password["\s]*[:=]\s*["\']?\w+["\']?', '[REDACTED]'),
            # Add more patterns as needed
        ]
        
        sanitized = data.copy()
        if isinstance(sanitized.get('content'), str):
            content = sanitized['content']
            for pattern, replacement in sensitive_patterns:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            sanitized['content'] = content
            
        return sanitized

    def log_llm_interaction(self, data: Dict):
        """Thread-safe logging of LLM interactions"""
        with self._lock:
            start_time = time.time()
            sanitized_data = self._sanitize_log_data(data)
            self.llm_history.append(sanitized_data)
            if len(self.llm_history) > self.max_history:
                self.llm_history = self.llm_history[-self.max_history:]
            self.logger.info("LLM Interaction", extra=sanitized_data)
            
            # Update metrics
            self.metrics['total_tokens'] += sanitized_data.get('token_usage', 0)
            self.metrics['total_calls'][sanitized_data.get('interaction_type')] += 1
            if not sanitized_data.get('success'):
                self.metrics['errors'][sanitized_data.get('error_type')] += 1
            self.metrics['response_times'].append(time.time() - start_time)
        
    def visualize_interactions(
        self,
        output_format: str = "text",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """Visualize LLM interactions within the specified time range.
        
        Args:
            output_format: Output format ("text" or "json")
            start_time: Filter interactions after this time
            end_time: Filter interactions before this time
            
        Returns:
            str: Formatted visualization of interactions
            
        Note: Currently only supports text format
        """
        if not self.llm_history:
            return "No interactions recorded"
        
        filtered_history = self.llm_history
        if start_time:
            filtered_history = [
                h for h in filtered_history 
                if h.get('timestamp', datetime.min) >= start_time
            ]
        if end_time:
            filtered_history = [
                h for h in filtered_history 
                if h.get('timestamp', datetime.max) <= end_time
            ]
        
        if output_format == "text":
            return "\n".join(
                f"[{h.get('timestamp', 'N/A')}] {h.get('message', 'No message')}"
                for h in filtered_history
            )
        if output_format == "json":
            raise NotImplementedError("JSON visualization not yet implemented")

        raise ValueError(f"Unsupported format: {output_format}")

    def get_analyzer(self) -> LLMInteractionAnalyzer:
        """Get an analyzer instance for the current logs."""
        if not self.log_dir:
            raise ValueError("No log directory configured")
        return LLMInteractionAnalyzer(self.log_dir)

    def get_visualizer(self) -> LLMInteractionVisualizer:
        """Get a visualizer instance for the current logs."""
        if not self.log_dir:
            raise ValueError("No log directory configured")
        return LLMInteractionVisualizer(self.log_dir)

    def log_completion(self, prompt: str, response: str, tokens: int, 
                       llm_name: str, llm_model,
                       success: bool = True):
        """Simplified logging for completion interactions"""
        self.log_llm_interaction({
            "llm_name": llm_name,
            "model": llm_model,
            "interaction_type": "completion",
            "content": prompt,
            "response": {
                "content": response,
                "usage": {"total_tokens": tokens}
            },
            "success": success
        })
    
    def log_error(self, error_type: str, message: str):
        """Simplified error logging"""
        self.log_llm_interaction({
            "interaction_type": "error",
            "error_type": error_type,
            "content": message,
            "success": False
        })

    @contextmanager
    def log_interaction_timing(self, metadata: Optional[Dict] = None):
        """Context manager for timing LLM interactions.
        
        Args:
            metadata: Optional dictionary containing additional interaction metadata
                     like phase, model, temperature, etc.
        
        Example:
            with logger.log_interaction_timing({"phase": "reasoning", "model": "gpt-4"}):
                response = llm.complete(prompt)
                logger.log_completion(prompt, response.text, response.tokens)
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Store timing with metadata
            timing_data = {
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat()
            }
            
            if metadata:
                timing_data.update(metadata)
                
            with self._lock:
                self.metrics['response_times'].append(timing_data)
