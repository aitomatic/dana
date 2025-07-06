"""
Output formatting for Dana REPL.

This module provides the OutputFormatter class that handles
formatting of execution results and error messages.
"""

from dana.common.error_utils import ErrorContext, ErrorHandler
from dana.common.mixins.loggable import Loggable
from dana.common.terminal_utils import ColorScheme


class OutputFormatter(Loggable):
    """Formats output and error messages for the Dana REPL."""

    def __init__(self, colors: ColorScheme):
        """Initialize with a color scheme."""
        super().__init__()
        self.colors = colors

    def format_result(self, result) -> None:
        """Format and display execution result."""
        if result is not None:
            print(f"{self.colors.accent(str(result))}")

    def format_error(self, error: Exception) -> None:
        """Format and display execution error."""
        context = ErrorContext("program execution")
        handled_error = ErrorHandler.handle_error(error, context)
        error_lines = handled_error.message.split("\n")
        formatted_error = "\n".join(f"  {line}" for line in error_lines)
        print(f"{self.colors.error('Error:')}\n{formatted_error}")

    def show_operation_cancelled(self) -> None:
        """Show operation cancelled message."""
        print("\nOperation cancelled")

    def show_goodbye(self) -> None:
        """Show goodbye message."""
        print("Goodbye! Dana REPL terminated.")
