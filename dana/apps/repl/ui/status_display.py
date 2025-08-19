"""
Status display utility for Dana REPL.

This module provides a simple way to display status information
at the bottom of the terminal without requiring complex layouts.
"""

import os
import sys
from typing import TYPE_CHECKING

from dana.common.mixins.loggable import Loggable

if TYPE_CHECKING:
    from dana.apps.repl.repl import Repl


class StatusDisplay(Loggable):
    """Simple status display that shows information at the bottom of the terminal."""

    def __init__(self, repl: "Repl"):
        """Initialize the status display."""
        super().__init__()
        self.repl = repl
        self.last_status = ""
        self.last_context = ""

    def get_terminal_size(self) -> tuple[int, int]:
        """Get the current terminal size (columns, rows)."""
        try:
            size = os.get_terminal_size()
            return size.columns, size.rows
        except Exception:
            return 80, 24  # Default fallback

    def get_context_info(self) -> str:
        """Get current context information."""
        try:
            # Count variables in different scopes
            var_count = 0
            func_count = 0
            context = self.repl.context

            for scope in ["private", "public", "local", "system"]:
                scope_vars = context._state.get(scope, {})
                for var_name, _ in scope_vars.items():
                    if not var_name.startswith("_"):  # Skip internal variables
                        var_count += 1

            # Count available functions
            try:
                registry = self.repl.interpreter.function_registry
                for scope in ["system", "private", "public"]:
                    functions = registry.list_functions(scope) or []
                    func_count += len(functions)
            except Exception:
                pass

            return f"Variables: {var_count} | Functions: {func_count} | Mode: Interactive"

        except Exception:
            return "Variables: ? | Functions: ? | Mode: Interactive"

    def show_status(self, message: str = "Ready", show_context: bool = True):
        """Display status information at the bottom of the terminal."""
        columns, rows = self.get_terminal_size()

        # Prepare status lines
        status_line1 = f"Dana REPL | {message}"
        status_line2 = self.get_context_info() if show_context else ""

        # Truncate lines if they're too long
        if len(status_line1) > columns - 2:
            status_line1 = status_line1[: columns - 5] + "..."
        if len(status_line2) > columns - 2:
            status_line2 = status_line2[: columns - 5] + "..."

        # Pad lines to full width for nice background
        status_line1 = f" {status_line1}".ljust(columns)
        status_line2 = f" {status_line2}".ljust(columns) if status_line2 else ""

        # Set scrolling region to reserve bottom 2 lines for status
        print(f"\033[1;{rows - 2}r", end="")  # Set scroll region to top to row-2

        # Move to bottom and print status
        print(f"\033[{rows - 1};1H", end="")  # Move to second-to-last row
        print(f"\033[44;37m{status_line1}\033[0m")  # Blue background, white text
        if status_line2:
            print(f"\033[{rows};1H", end="")  # Move to last row
            print(f"\033[44;37m{status_line2}\033[0m")  # Blue background, white text

        # Move cursor back to main area (above status bar)
        print(f"\033[{rows - 3};1H", end="")  # Move to row above status
        sys.stdout.flush()

        self.last_status = message
        self.last_context = status_line2

    def show_error(self, error_msg: str):
        """Display an error message in the status area."""
        columns, rows = self.get_terminal_size()

        # Truncate long error messages
        if len(error_msg) > columns - 20:
            error_msg = error_msg[: columns - 23] + "..."

        error_line = f" Dana REPL | Error: {error_msg}".ljust(columns)
        context_line = f" {self.get_context_info()}".ljust(columns)

        # Set scrolling region to reserve bottom 2 lines for status
        print(f"\033[1;{rows - 2}r", end="")  # Set scroll region to top to row-2

        # Move to bottom and print error status
        print(f"\033[{rows - 1};1H", end="")  # Move to second-to-last row
        print(f"\033[41;37;1m{error_line}\033[0m")  # Red background, white bold text
        print(f"\033[{rows};1H", end="")  # Move to last row
        print(f"\033[44;37m{context_line}\033[0m")  # Blue background, white text

        # Move cursor back to main area (above status bar)
        print(f"\033[{rows - 3};1H", end="")  # Move to row above status
        sys.stdout.flush()

    def clear_status(self):
        """Clear the status display area."""
        columns, rows = self.get_terminal_size()

        # Reset scroll region to full screen
        print(f"\033[1;{rows}r", end="")  # Reset scroll region to full screen

        # Clear the last two lines
        print(f"\033[{rows - 1};1H", end="")  # Move to second-to-last row
        print(" " * columns)
        print(f"\033[{rows};1H", end="")  # Move to last row
        print(" " * columns)

        sys.stdout.flush()

    def update_if_changed(self, message: str = "Ready"):
        """Update status only if it has changed (for performance)."""
        current_context = self.get_context_info()
        if self.last_status != message or self.last_context != current_context:
            self.show_status(message)
