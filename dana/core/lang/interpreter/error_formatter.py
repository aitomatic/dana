"""
Enhanced error formatter for Dana runtime errors.

This module provides comprehensive error formatting with file location,
line numbers, source code context, and stack traces.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

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
        import re  # Ensure re is available in this method

        # Minimal, caret-style formatting for parse errors
        error_msg = str(error)
        if ("Unexpected token" in error_msg) or ("No terminal matches" in error_msg):
            # Extract line/column
            line_match = re.search(r"line (\d+), col(?:umn)? (\d+)", error_msg)
            line_num = None
            col_num = None
            if line_match:
                line_num = int(line_match.group(1))
                col_num = int(line_match.group(2))

            # Resolve source line from error context if available
            source_line = ""
            if error_context and line_num:
                # Prefer explicit filename; fallback to current_file
                if error_context.current_location and error_context.current_location.filename:
                    source_line = error_context.get_source_line(error_context.current_location.filename, line_num) or ""
                elif error_context.current_file:
                    source_line = error_context.get_source_line(error_context.current_file, line_num) or ""

            # Try to extract unexpected token for context-specific hinting
            token_match = re.search(r"Unexpected token Token\('([^']+)', '([^']+)'\)", error_msg)
            token_value = token_match.group(2) if token_match else None

            # Check for inheritance syntax attempts
            if source_line and "(" in source_line and ")" in source_line:
                # Look for inheritance patterns: struct/resource/agent_blueprint Name(Parent):
                inheritance_patterns = [
                    (r"struct\s+(\w+)\s*\(\s*(\w+)\s*\)", "struct"),
                    (r"resource\s+(\w+)\s*\(\s*(\w+)\s*\)", "resource"),
                    (r"agent_blueprint\s+(\w+)\s*\(\s*(\w+)\s*\)", "agent_blueprint"),
                    (r"workflow\s+(\w+)\s*\(\s*(\w+)\s*\)", "workflow"),
                ]

                for pattern, type_name in inheritance_patterns:
                    match = re.search(pattern, source_line)
                    if match:
                        child_name, parent_name = match.groups()
                        lines = [
                            f"Dana does not support inheritance for {type_name}s.",
                            f"  Input: {source_line.strip()}",
                            "",
                            "Instead of inheritance, use composition:",
                            f"  {type_name} {child_name}:",
                            f"    _parent: {parent_name}  # Composition with delegation",
                            "    # Add your own fields here",
                            "",
                            "Then access parent fields via delegation:",
                            f"  instance = {child_name}()",
                            "  instance.parent_field  # Delegated from _parent",
                            "",
                            "Learn more: https://docs.dana-lang.org/structs#composition-and-delegation",
                        ]
                        return "\n".join(lines)

            # Build minimal message
            header = "Syntax Error"
            if line_num is not None and col_num is not None:
                header = f"Syntax Error (line {line_num}, column {col_num})"

            caret = ""
            if col_num is not None:
                caret = (" " * (col_num - 1)) + "^"

            lines = [header]
            if source_line:
                lines.append(source_line)
                if caret:
                    lines.append(caret)

            # Minimal, single-line hint for common reserved keyword misuse
            if token_value == "resource":
                lines.append(
                    "hint: 'resource' is reserved; rename the receiver to the resource type or 'self' (e.g., def (bicycle: Type) method(...):)"
                )
            return "\n".join(lines)

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
        elif "Function" in error_msg and "not found" in error_msg:
            # Extract function name from error message
            import re

            func_match = re.search(r"Function '([^']+)'", error_msg)
            if func_match:
                func_name = func_match.group(1)
                lines.append(f"Root cause: Function '{func_name}' is not available in the current scope")
                lines.append("Suggested fix: Import the function using one of these methods:")
                lines.append(f'  • use("{func_name}")  # Import from stdlib (if use() is available)')
                lines.append(f"  • import stdlib.core.{func_name}_functions  # Full import")
                lines.append("  • Check if the function is available in the current namespace")

                # Provide specific guidance for common functions
                if func_name in ["reason", "llm", "log", "print", "agent"]:
                    lines.append("")
                    lines.append("Note: These are stdlib functions that require explicit import.")
                    lines.append("If use() is not available, try:")
                    lines.append(f"  • import stdlib.core.{func_name}_function")
                    lines.append("  • Or check if the function is available in your Dana environment")

                # Suggest similar function names
                similar_functions = []
                if func_name == "no":
                    similar_functions.append("noop")
                elif func_name == "yes":
                    similar_functions.append("noop")
                elif func_name == "prnt":
                    similar_functions.append("print")
                elif func_name == "logg":
                    similar_functions.append("log")

                if similar_functions:
                    lines.append("")
                    lines.append("Did you mean:")
                    for similar_func in similar_functions:
                        lines.append(f"  • {similar_func}()")
            else:
                lines.append("Root cause: Function not found in the current scope")
                lines.append("Suggested fix: Import the function using use() or import statements")
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
