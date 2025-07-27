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

    type: str  # Exception class name
    message: str  # Error message
    traceback: list[str]  # Stack trace lines
    original: Exception  # Python exception object
    filename: str | None = None  # File where error occurred
    line: int | None = None  # Line number where error occurred
    column: int | None = None  # Column number where error occurred
    source_line: str | None = None  # Source code line where error occurred

    def __str__(self) -> str:
        """String representation of the exception."""
        location_info = ""
        if self.filename:
            location_info = f' (File "{self.filename}"'
            if self.line is not None:
                location_info += f", line {self.line}"
            if self.column is not None:
                location_info += f", column {self.column}"
            location_info += ")"
        return f"{self.type}: {self.message}{location_info}"

    def to_dict(self) -> dict[str, any]:
        """Convert to dictionary for easy access in Dana."""
        result = {
            "type": self.type,
            "message": self.message,
            "traceback": self.traceback,
        }
        if self.filename:
            result["filename"] = self.filename
        if self.line is not None:
            result["line"] = self.line
        if self.column is not None:
            result["column"] = self.column
        if self.source_line:
            result["source_line"] = self.source_line
        return result


def create_dana_exception(exc: Exception, error_context=None) -> DanaException:
    """Convert a Python exception to a Dana exception object.

    Args:
        exc: The Python exception to convert
        error_context: Optional ErrorContext with location information

    Returns:
        A DanaException object with accessible properties
    """
    # Get the traceback if available
    tb_lines = []
    if hasattr(exc, "__traceback__") and exc.__traceback__:
        tb_lines = traceback.format_tb(exc.__traceback__)

    # Extract location information from error context
    filename = None
    line = None
    column = None
    source_line = None

    if error_context is not None:
        from dana.core.lang.interpreter.error_context import ErrorContext

        if isinstance(error_context, ErrorContext) and error_context.current_location:
            loc = error_context.current_location
            filename = loc.filename
            line = loc.line
            column = loc.column
            source_line = loc.source_line

    return DanaException(
        type=type(exc).__name__,
        message=str(exc),
        traceback=tb_lines,
        original=exc,
        filename=filename,
        line=line,
        column=column,
        source_line=source_line,
    )
