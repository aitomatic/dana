"""
Input state management for Dana REPL.

This module provides the InputState class that tracks multiline input
and manages the input buffer.
"""

from typing import List

from opendxa.common.mixins.loggable import Loggable


class InputState(Loggable):
    """Tracks the state of multiline input."""

    def __init__(self):
        """Initialize the input state."""
        super().__init__()
        self.buffer: List[str] = []
        self.in_multiline = False

    def add_line(self, line: str) -> None:
        """Add a line to the buffer."""
        self.buffer.append(line)

    def get_buffer(self) -> str:
        """Get the current buffer as a string."""
        return "\n".join(self.buffer)

    def reset(self) -> None:
        """Reset the buffer."""
        self.buffer = []
        self.in_multiline = False

    def has_content(self) -> bool:
        """Check if the buffer has any non-empty content."""
        return any(line.strip() for line in self.buffer)

    def is_empty(self) -> bool:
        """Check if the buffer is empty."""
        return not self.buffer or not self.has_content()
