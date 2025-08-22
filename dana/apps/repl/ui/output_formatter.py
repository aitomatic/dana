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
        self._progress_shown = False

    def format_result(self, result) -> None:
        """Format and display execution result."""
        if result is not None:
            # Use consolidated Promise detection
            try:
                from dana.core.concurrency import is_promise

                if is_promise(result):
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
            # Use consolidated Promise detection
            try:
                from dana.core.concurrency import is_promise

                if is_promise(result):
                    # Show the promise object itself (don't await)
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

    async def show_progress(self, message: str) -> None:
        """Show a progress indicator."""
        if not self._progress_shown:
            print(f"\n⏳ {message}", end="", flush=True)
            self._progress_shown = True

    async def update_progress(self, message: str) -> None:
        """Update the progress message."""
        if self._progress_shown:
            print(f"\r⏳ {message}", end="", flush=True)

    async def hide_progress(self) -> None:
        """Hide the progress indicator."""
        if self._progress_shown:
            print("\r" + " " * 80 + "\r", end="", flush=True)
            self._progress_shown = False

    async def show_cancelled(self) -> None:
        """Show cancellation message."""
        print("\n⏹️  Operation cancelled by user")

    async def show_completed(self, elapsed_time: float) -> None:
        """Show completion message."""
        print(f"\n✅ Completed in {elapsed_time:.1f}s")
