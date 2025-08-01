"""
Enhanced error formatter for Dana runtime errors.

This module provides comprehensive error formatting with file location,
line numbers, source code context, and stack traces.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import re

from dana.common.error_utils import ErrorUtils
from dana.core.lang.interpreter.error_context import ErrorContext


class EnhancedErrorFormatter:
    """Format errors with comprehensive location and context information."""

    @staticmethod
    def format_error(error: Exception, error_context: ErrorContext | None = None, show_traceback: bool = True) -> str:
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
                # Extract just the filename without the full path for cleaner display
                import os

                filename = os.path.basename(loc.filename) if loc.filename else "unknown"
                location_parts.append(f'File "{filename}"')
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
    def format_developer_error(error: Exception, error_context: ErrorContext | None = None, show_traceback: bool = True) -> str:
        """Format an error in a clean, developer-friendly format (Option 3).

        Args:
            error: The exception to format
            error_context: Optional error context with location information
            show_traceback: Whether to include the full traceback

        Returns:
            Formatted error message in clean developer format
        """
        # Check for reserved keyword errors first
        error_msg = str(error)
        previous_tokens = []  # Initialize to avoid scoping issues

        if "Unexpected token" in error_msg:
            # Try to extract error details
            line_match = re.search(r"line (\d+), col(?:umn)? (\d+)", error_msg)
            token_match = re.search(r"Unexpected token Token\('([^']+)', '([^']+)'\)", error_msg)

            if token_match:
                token_type, token_value = token_match.groups()

                # Check if this is a reserved keyword error (either direct or in previous tokens)
                is_reserved_keyword_error = False
                actual_keyword = None

                if token_value in ErrorUtils.RESERVED_KEYWORDS:
                    is_reserved_keyword_error = True
                    actual_keyword = token_value
                else:
                    # Check if a reserved keyword is in the previous tokens
                    previous_match = re.search(r"Previous tokens: \[(.*?)\]", error_msg)
                    if previous_match:
                        previous_text = previous_match.group(1)
                        # The previous tokens are in format: Token('AGENT', 'agent')
                        # We need to extract all Token(...) patterns properly
                        token_patterns = re.findall(r"Token\('([^']+)', '([^']+)'\)", previous_text)
                        previous_tokens = []
                        for token_type, token_value in token_patterns:
                            previous_tokens.append(f"Token('{token_type}', '{token_value}')")

                        # Use the shared method to find reserved keywords
                        actual_keyword = ErrorUtils._find_reserved_keyword_in_tokens(previous_tokens)
                        if actual_keyword:
                            is_reserved_keyword_error = True

                if is_reserved_keyword_error and actual_keyword:
                    # Extract expected tokens
                    expected_tokens = []

                    # Parse expected tokens
                    expected_match = re.search(r"Expected one of:\s*(.*?)(?:\n|$)", error_msg, re.DOTALL)
                    if expected_match:
                        expected_text = expected_match.group(1)
                        expected_tokens = [line.strip().replace("*", "").strip() for line in expected_text.split("\n") if line.strip()]

                    # Detect context
                    context = ErrorUtils.detect_reserved_keyword_context(error_msg, expected_tokens, previous_tokens)

                    if context and line_match:
                        line_num = int(line_match.group(1))
                        column_num = int(line_match.group(2))

                        # Get source line if available
                        source_line = ""
                        if error_context and error_context.current_file and line_num:
                            source_line = error_context.get_source_line(error_context.current_file, line_num) or ""

                        # Create enhanced error message
                        enhanced_msg = ErrorUtils.create_reserved_keyword_error_message(
                            actual_keyword, context, line_num, column_num, source_line
                        )
                        return enhanced_msg

        # Fall back to original formatting for non-reserved keyword errors
        lines = []

        # Header
        lines.append("=== Dana Runtime Error ===")

        # File information
        filename = "unknown file"
        if error_context and error_context.current_location and error_context.current_location.filename:
            import os

            filename = os.path.basename(error_context.current_location.filename)
        elif error_context and error_context.current_file:
            import os

            filename = os.path.basename(error_context.current_file)

        lines.append(f"File: {filename}")

        # Error type and message
        error_type = type(error).__name__
        error_msg = str(error)
        lines.append(f"Error: {error_type} - {error_msg}")

        # Execution trace if available
        if error_context and error_context.execution_stack:
            lines.append("")
            lines.append("Execution Trace:")
            for i, loc in enumerate(error_context.execution_stack, 1):
                location_desc = []
                if loc.line is not None:
                    location_desc.append(f"Line {loc.line}")
                if loc.column is not None:
                    location_desc.append(f"column {loc.column}")
                if loc.function_name:
                    location_desc.append(loc.function_name)

                location_str = ", ".join(location_desc) if location_desc else "unknown location"
                lines.append(f"{i}. {location_str}")

                # Show the actual source code if available
                if loc.filename and loc.line:
                    source_line = error_context.get_source_line(loc.filename, loc.line)
                    if source_line and len(source_line.strip()) > 0:
                        # Truncate long lines for better readability
                        display_line = source_line.strip()
                        if len(display_line) > 40:
                            display_line = display_line[:37] + "..."
                        lines.append(f"   Code: {display_line}")

        # Root cause analysis for common errors
        lines.append("")
        if "NoneType" in error_msg and "attribute" in error_msg:
            lines.append("Root cause: Attempted to access an attribute on a None value")
            lines.append("Suggested fix: Check that the function returns a valid object before accessing its attributes")
        elif "missing" in error_msg and "argument" in error_msg:
            lines.append("Root cause: Function called with missing required arguments")
            lines.append("Suggested fix: Check function signature and provide all required arguments")
        elif "not defined" in error_msg:
            lines.append("Root cause: Attempted to use an undefined variable or function")
            lines.append("Suggested fix: Check spelling and ensure variable/function is defined before use")
        else:
            lines.append("Problem: See error message above")
            lines.append("Debug tip: Check the execution trace above for the source of the error")

        return "\n".join(lines)

    @staticmethod
    def format_simple_error(error: Exception, filename: str | None = None) -> str:
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
