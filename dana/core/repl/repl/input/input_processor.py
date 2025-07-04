"""
Input processing logic for Dana REPL.

This module provides the InputProcessor class that coordinates
input state management and completeness checking.
"""

from dana.common.mixins.loggable import Loggable

from .completeness_checker import InputCompleteChecker
from .input_state import InputState


class InputProcessor(Loggable):
    """Processes and manages user input for the Dana REPL."""

    def __init__(self):
        """Initialize the input processor."""
        super().__init__()
        self.state = InputState()
        self.checker = InputCompleteChecker()

    def process_line(self, line: str) -> tuple[bool, str | None]:
        """Process a single input line.

        Args:
            line: The input line to process

        Returns:
            A tuple of (should_continue, executed_program)
            - should_continue: True if we should continue to next iteration
            - executed_program: The executed program if any, None otherwise
        """
        # Handle empty lines
        if not line.strip() and not self.state.in_multiline:
            self.debug("Empty line, continuing")
            return True, None

        if not line.strip() and self.state.in_multiline:
            self.debug("Empty line in multiline mode, executing buffer")
            program = self._execute_multiline_buffer()
            return True, program

        # Check if input is obviously incomplete
        if self.checker.is_obviously_incomplete(line):
            self.debug("Obviously incomplete input, entering multiline mode")
            self.state.in_multiline = True
            self.state.add_line(line)
            return True, None

        # If we're already in multiline mode, just add the line
        if self.state.in_multiline:
            self.debug("Adding line to multiline buffer")
            self.state.add_line(line)
            return True, None

        # For single-line input, return False to indicate it should be executed
        return False, None

    def _execute_multiline_buffer(self) -> str | None:
        """Get the multiline buffer content and reset state.

        Returns:
            The program string if successful, None otherwise
        """
        program = self.state.get_buffer()
        self.state.reset()

        if program.strip():  # Only return if there's actual content
            return program
        return None

    def reset(self) -> None:
        """Reset the input processor state."""
        self.state.reset()

    def is_orphaned_else_statement(self, line: str) -> bool:
        """Check if the line is an orphaned else/elif statement."""
        stripped = line.strip()
        return (stripped.startswith("else:") or stripped.startswith("elif ")) and not self.state.in_multiline

    @property
    def in_multiline(self) -> bool:
        """Check if currently in multiline mode."""
        return self.state.in_multiline
