"""
Output formatting for Dana REPL.

This module provides the OutputFormatter class that handles
formatting of execution results and error messages.
"""

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.shortcuts import print_formatted_text

from dana.common.error_utils import ErrorContext, ErrorHandler
from dana.common.mixins.loggable import Loggable
from dana.common.terminal_utils import ColorScheme


class OutputFormatter(Loggable):
    """Formats output and error messages for the Dana REPL."""

    def __init__(self, colors: ColorScheme):
        """Initialize output formatter."""
        super().__init__()
        self.colors = colors

    def format_result(self, result) -> None:
        """Format and display execution result."""
        if result is not None:
            # Import promise classes to check instance
            try:
                from dana.core.concurrency import BasePromise

                if isinstance(result, BasePromise):
                    # Always show promise meta info instead of resolving
                    print_formatted_text(ANSI(self.colors.accent(str(result))))
                    return
            except ImportError:
                # If promise classes not available, fall back to normal display
                pass

            # Normal display - show the resolved value
            print_formatted_text(ANSI(self.colors.accent(str(result))))

    async def format_result_async(self, result) -> None:
        """Format and display execution result, safe for async contexts."""
        if result is not None:
            # Import promise classes to check instance
            try:
                from dana.core.concurrency import BasePromise
                from dana.core.concurrency.eager_promise import EagerPromise

                if isinstance(result, EagerPromise):
                    # For EagerPromise, use async-safe resolution
                    try:
                        resolved_result = await result.await_result()
                        print_formatted_text(ANSI(self.colors.accent(str(resolved_result))))
                        return
                    except Exception as e:
                        # If resolution fails, show the promise meta info with error
                        print_formatted_text(ANSI(self.colors.accent(f"EagerPromise[Error: {e}]")))
                        return
                elif isinstance(result, BasePromise):
                    # For other promise types, show meta info instead of resolving
                    print_formatted_text(ANSI(self.colors.accent(str(result))))
                    return
            except ImportError:
                # If promise classes not available, fall back to normal display
                pass

            # Normal display - show the resolved value with color
            print_formatted_text(ANSI(self.colors.accent(str(result))))

    def format_error(self, error: Exception) -> None:
        """Format and display execution error."""
        context = ErrorContext("program execution")
        handled_error = ErrorHandler.handle_error(error, context)
        error_lines = handled_error.message.split("\n")
        formatted_error = "\n".join(f"  {line}" for line in error_lines)
        print_formatted_text(ANSI(f"{self.colors.error('Error:')}\n{formatted_error}"))

    def show_operation_cancelled(self) -> None:
        """Show operation cancelled message."""
        print("Operation cancelled")

    def show_goodbye(self) -> None:
        """Show goodbye message."""
        print("Goodbye! Dana REPL terminated.")
