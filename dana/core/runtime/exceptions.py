"""
Dana exception object for exception handling in Dana programs.

This module provides the DanaException class that wraps Python exceptions
and makes their properties accessible to Dana code.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import traceback
from dataclasses import dataclass


@dataclass
class DanaException:
    """Dana exception object with accessible properties.
    
    This class wraps Python exceptions and provides access to their
    properties in a way that Dana programs can use.
    """
    
    type: str              # Exception class name
    message: str           # Error message
    traceback: list[str]   # Stack trace lines
    original: Exception    # Python exception object
    
    def __str__(self) -> str:
        """String representation of the exception."""
        return f"{self.type}: {self.message}"
    
    
    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary for easy access in Dana."""
        return {
            "type": self.type,
            "message": self.message,
            "traceback": self.traceback,
        }


def create_dana_exception(exc: Exception) -> DanaException:
    """Convert a Python exception to a Dana exception object.
    
    Args:
        exc: The Python exception to convert
        
    Returns:
        A DanaException object with accessible properties
    """
    # Get the traceback if available
    tb_lines = []
    if hasattr(exc, "__traceback__") and exc.__traceback__:
        tb_lines = traceback.format_tb(exc.__traceback__)
    
    return DanaException(
        type=type(exc).__name__,
        message=str(exc),
        traceback=tb_lines,
        original=exc
    )