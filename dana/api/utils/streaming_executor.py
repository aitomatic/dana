"""
Streaming Executor for Real-time Log Output

This module provides a custom executor that can stream print output in real-time
via WebSocket connections during .na file execution.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Union

from dana.core.lang.interpreter.executor.dana_executor import DanaExecutor
from dana.registry import FunctionRegistry


class StreamingExecutor(DanaExecutor):
    """
    Custom executor that can stream print output in real-time.

    This executor extends DanaExecutor to intercept output buffer writes
    and stream them immediately via WebSocket instead of just buffering.
    """

    def __init__(
        self,
        function_registry: FunctionRegistry | None = None,
        enable_optimizations: bool = True,
        log_streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]] | None = None,
    ):
        """
        Initialize the streaming executor.

        Args:
            function_registry: Optional function registry
            enable_optimizations: Whether to enable AST traversal optimizations
            log_streamer: Optional callback for streaming log messages in real-time.
                         Signature: log_streamer(level: str, message: str)
                         Can be sync or async function.
        """
        super().__init__(function_registry, enable_optimizations)
        self._log_streamer = log_streamer
        self._original_output_buffer = self._output_buffer

        # Override the output buffer to enable streaming
        if log_streamer:
            self._output_buffer = StreamingOutputBuffer(original_buffer=self._original_output_buffer, log_streamer=log_streamer)

    def set_log_streamer(self, log_streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]]) -> None:
        """
        Set or update the log streamer callback.

        Args:
            log_streamer: Callback for streaming log messages in real-time
        """
        self._log_streamer = log_streamer

        # Update the output buffer if needed
        if isinstance(self._output_buffer, StreamingOutputBuffer):
            self._output_buffer.set_log_streamer(log_streamer)
        else:
            # Convert regular buffer to streaming buffer
            self._output_buffer = StreamingOutputBuffer(original_buffer=self._original_output_buffer, log_streamer=log_streamer)


class StreamingOutputBuffer:
    """
    A custom output buffer that streams log messages in real-time while also buffering them.

    This class acts as a drop-in replacement for a regular list buffer, but it immediately
    streams each message when it's added.
    """

    def __init__(self, original_buffer: list, log_streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]]):
        """
        Initialize the streaming output buffer.

        Args:
            original_buffer: The original list buffer to maintain compatibility
            log_streamer: Callback for streaming log messages
        """
        self._original_buffer = original_buffer
        self._log_streamer = log_streamer

    def set_log_streamer(self, log_streamer: Union[Callable[[str, str], None], Callable[[str, str], Awaitable[None]]]) -> None:
        """Update the log streamer callback."""
        self._log_streamer = log_streamer

    def append(self, message: str) -> None:
        """
        Append a message to the buffer and stream it immediately.

        Args:
            message: The log message to add
        """
        # Add to original buffer for compatibility
        self._original_buffer.append(message)

        # Stream immediately if streamer is available
        if self._log_streamer:
            self._stream_message("info", message)

    def _stream_message(self, level: str, message: str) -> None:
        """
        Stream a log message via the callback.

        Args:
            level: Log level (info, warning, error, etc.)
            message: The message to stream
        """
        try:
            result = self._log_streamer(level, message)

            # Handle async streaming
            if asyncio.iscoroutine(result):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If we're in an async context, create a task
                        asyncio.create_task(result)
                    else:
                        # If not in async context, run until complete
                        loop.run_until_complete(result)
                except RuntimeError:
                    # No event loop running, try to create one
                    try:
                        asyncio.run(result)
                    except Exception as e:
                        print(f"Warning: Async log streamer failed: {e}")
        except Exception as e:
            # Don't let streaming errors break execution
            print(f"Warning: Log streamer failed: {e}")

    def clear(self) -> None:
        """Clear the buffer."""
        self._original_buffer.clear()

    def __len__(self) -> int:
        """Return the length of the buffer."""
        return len(self._original_buffer)

    def __iter__(self):
        """Iterate over the buffer."""
        return iter(self._original_buffer)

    def __getitem__(self, index):
        """Get item from buffer by index."""
        return self._original_buffer[index]

    def __setitem__(self, index, value):
        """Set item in buffer by index."""
        self._original_buffer[index] = value
