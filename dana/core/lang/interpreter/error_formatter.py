"""
Enhanced error formatter for Dana runtime errors.

This module provides comprehensive error formatting with file location,
line numbers, source code context, and stack traces.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Optional

from dana.common.exceptions import DanaError
from dana.core.lang.interpreter.error_context import ErrorContext


class EnhancedErrorFormatter:
    """Format errors with comprehensive location and context information."""
    
    @staticmethod
    def format_error(
        error: Exception,
        error_context: Optional[ErrorContext] = None,
        show_traceback: bool = True
    ) -> str:
        """Format an error with location and context information.
        
        Args:
            error: The exception to format
            error_context: Optional error context with location information
            show_traceback: Whether to include the full traceback
            
        Returns:
            Formatted error message with location and context
        """
        lines = []
        
        # Add traceback if available and requested
        if show_traceback and error_context and error_context.execution_stack:
            lines.append(error_context.format_stack_trace())
            lines.append("")  # Empty line separator
        
        # Format the main error
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Add location information if available
        if error_context and error_context.current_location:
            loc = error_context.current_location
            
            # Main error line with location
            location_parts = []
            if loc.filename:
                location_parts.append(f'File "{loc.filename}"')
            if loc.line is not None:
                location_parts.append(f"line {loc.line}")
            if loc.column is not None:
                location_parts.append(f"column {loc.column}")
            
            if location_parts:
                lines.append(f"{error_type}: {error_msg}")
                lines.append(f"  {', '.join(location_parts)}")
            else:
                lines.append(f"{error_type}: {error_msg}")
            
            # Add source code context
            if loc.filename and loc.line:
                source_line = error_context.get_source_line(loc.filename, loc.line)
                if source_line:
                    lines.append("")
                    lines.append("    " + source_line)
                    if loc.column:
                        lines.append("    " + " " * (loc.column - 1) + "^")
            elif loc.line and error_context.current_file:
                # Try to get source line from current file if filename not in location
                source_line = error_context.get_source_line(error_context.current_file, loc.line)
                if source_line:
                    lines.append("")
                    lines.append("    " + source_line)
                    if loc.column:
                        lines.append("    " + " " * (loc.column - 1) + "^")
        else:
            # No location information available
            lines.append(f"{error_type}: {error_msg}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_simple_error(error: Exception, filename: Optional[str] = None) -> str:
        """Format a simple error message without full context.
        
        Args:
            error: The exception to format
            filename: Optional filename where the error occurred
            
        Returns:
            Simple formatted error message
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        if filename:
            return f"{error_type}: {error_msg} (in {filename})"
        else:
            return f"{error_type}: {error_msg}"