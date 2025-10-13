"""Console I/O resource implementation for Dana.

This module provides a console-based implementation of the BaseIOResource interface,
allowing interaction through standard input/output streams.
"""

from typing import Any

from .base_io import BaseIO


class ConsoleIO(BaseIO):
    """Console-based I/O resource implementation.

    This class implements the BaseIOResource interface for console-based interaction,
    using standard input/output streams.
    """

    def __init__(self, name: str = "console", description: str | None = None):
        """Initialize console I/O resource."""
        super().__init__(name, description or "Console-based I/O resource")
        self._buffer: list[str] = []  # For testing purposes

    async def send(self, message: Any) -> None:
        """Print to console."""
        print(message)
        self._buffer.append(str(message))

    async def receive(self) -> Any:
        """Get input from console."""
        return input("> ")

    async def initialize(self) -> None:
        """Initialize console I/O."""
        await super().initialize()
        self.info("Console I/O resource initialized")

    async def cleanup(self) -> None:
        """Clean up console I/O."""
        await super().cleanup()
        self.info("Console I/O resource cleaned up")
