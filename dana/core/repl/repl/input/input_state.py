"""
Input state management for Dana REPL.

This module provides the InputState class that tracks multiline input
and manages the input buffer.
"""

from collections import deque

from dana.common.mixins.loggable import Loggable


class InputState(Loggable):
    """Tracks the state of multiline input."""

    def __init__(self):
        """Initialize the input state."""
        super().__init__()
        self.buffer: list[str] = []
        self.in_multiline = False
        # Track input history for IPV context analysis (current line + 4 previous)
        self.input_history: deque = deque(maxlen=5)

    def add_line(self, line: str) -> None:
        """Add a line to the buffer and track in history."""
        self.buffer.append(line)
        # Also add to input history for IPV context
        self.input_history.append(line)

    def add_to_history(self, line: str) -> None:
        """Add a line to the input history (for single-line commands)."""
        self.input_history.append(line)

    def get_buffer(self) -> str:
        """Get the current buffer as a string."""
        return "\n".join(self.buffer)

    def get_input_history(self) -> list[str]:
        """Get the recent input history as a list (most recent first)."""
        return list(reversed(self.input_history))

    def get_input_context(self) -> str:
        """Get the input history formatted for IPV context analysis."""
        if not self.input_history:
            return ""

        # Return lines in chronological order (oldest to newest)
        lines = list(self.input_history)
        return "\n".join(lines)

    def reset(self) -> None:
        """Reset the buffer."""
        self.buffer = []
        self.in_multiline = False
        # Note: We don't reset input_history here to preserve context across commands

    def has_content(self) -> bool:
        """Check if the buffer has any non-empty content."""
        return any(line.strip() for line in self.buffer)

    def is_empty(self) -> bool:
        """Check if the buffer is empty."""
        return not self.buffer or not self.has_content()
