"""Logging configuration for DXA."""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict
from datetime import datetime
from .log_analysis import LLMInteractionAnalyzer
from .log_viz import LLMInteractionVisualizer

__all__ = ['DXALogger']  # Export the class

class DXALogger:
    """Unified logging for DXA system"""
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        log_level: str = "INFO",
        **kwargs
    ):
        self.log_dir = log_dir  # Store log_dir as instance variable
        self.configure_logging(log_dir, log_level, **kwargs)
        self.llm_history = []
        
    def configure_logging(self, log_dir: Optional[str], log_level: str, **kwargs):
        """Configure system-wide logging"""
        # Create root logger
        self.logger = logging.getLogger('dxa')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatters
        json_format = kwargs.get('json_format', False)
        if json_format:
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "logger": "%(name)s", '
                '"level": "%(levelname)s", "message": "%(message)s"}'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
        
        # Set up console logging if requested
        console_output = kwargs.get('console_output', True)
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
    def log_llm_interaction(self, data: Dict):
        """Log LLM interaction with visualization support"""
        self.llm_history.append(data)
        self.logger.info("LLM Interaction", extra={"interaction_data": data})
        
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
        elif output_format == "json":
            raise NotImplementedError("JSON visualization not yet implemented")
        else:
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
