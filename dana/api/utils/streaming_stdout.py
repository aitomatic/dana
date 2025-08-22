"""
Streaming stdout capture for real-time log streaming.

This module provides a custom stdout that can stream output in real-time
while maintaining compatibility with normal stdout operations.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import sys
import io
from typing import Union
from collections.abc import Callable, Awaitable


class StreamingStdout(io.StringIO):
    """
    A custom stdout replacement that streams output in real-time.

    This class extends StringIO to capture stdout while also streaming
    each line immediately via a callback function.
    """

    def __init__(
        self, original_stdout=None, log_streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]] | None = None
    ):
        """
        Initialize the streaming stdout.

        Args:
            original_stdout: The original stdout to restore later
            log_streamer: Callback for streaming log messages in real-time
        """
        super().__init__()
        self._original_stdout = original_stdout or sys.stdout
        self._log_streamer = log_streamer
        self._buffer = ""

    def write(self, text: str) -> int:
        """
        Write text to both the buffer and stream it if it contains newlines.

        Args:
            text: Text to write

        Returns:
            Number of characters written
        """
        # Write to the internal buffer for compatibility
        result = super().write(text)

        # Note: Don't write to original stdout to avoid recursive loops
        # The captured content will be streamed via the callback instead

        # Handle streaming for complete lines
        self._buffer += text

        # Stream complete lines immediately
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip() and self._log_streamer:  # Only stream non-empty lines
                self._stream_line(line.strip())

        return result

    def _stream_line(self, line: str) -> None:
        """
        Stream a complete line via the callback.

        Args:
            line: The line to stream
        """
        if self._log_streamer:
            try:
                self._log_streamer("info", line)
            except Exception as e:
                # Don't let streaming errors break execution
                print(f"Warning: Log streaming failed: {e}", file=self._original_stdout)

    def flush(self) -> None:
        """Flush the stream."""
        super().flush()

        # Stream any remaining buffer content on flush
        if self._buffer.strip() and self._log_streamer:
            self._stream_line(self._buffer.strip())
            self._buffer = ""


class StdoutContextManager:
    """Context manager for temporarily replacing stdout with streaming version."""

    def __init__(self, log_streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]] | None = None):
        """
        Initialize the context manager.

        Args:
            log_streamer: Callback for streaming log messages
        """
        self._log_streamer = log_streamer
        self._original_stdout = None
        self._streaming_stdout = None

    def __enter__(self) -> "StreamingStdout":
        """Enter the context and replace stdout."""
        self._original_stdout = sys.stdout
        self._streaming_stdout = StreamingStdout(original_stdout=self._original_stdout, log_streamer=self._log_streamer)
        sys.stdout = self._streaming_stdout
        return self._streaming_stdout

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and restore original stdout."""
        if self._streaming_stdout:
            self._streaming_stdout.flush()
        sys.stdout = self._original_stdout
