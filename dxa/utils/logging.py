"""Logging configuration for DXA."""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional

__all__ = ['configure_logging']  # Export the function

def configure_logging(
    log_dir: Optional[str] = None,
    log_level: str = "INFO",
    json_format: bool = True,
    console_output: bool = True,
    max_bytes: int = 10_000_000,
    backup_count: int = 5,
    when: str = 'midnight',
    compress: bool = True,
    cleanup_days: Optional[int] = 30
) -> None:
    """Configure logging for DXA."""
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatters
    if json_format:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        main_handler.setFormatter(formatter)
        root_logger.addHandler(main_handler)
        
        # LLM interactions log file - rotate daily
        llm_handler = TimedRotatingFileHandler(
            os.path.join(log_dir, 'llm_interactions.log'),
            when=when,
            interval=1,
            backupCount=backup_count
        )
        llm_handler.setFormatter(formatter)
        llm_logger = logging.getLogger('dxa.llm')
        llm_logger.addHandler(llm_handler)
    
    # Set up console logging if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
