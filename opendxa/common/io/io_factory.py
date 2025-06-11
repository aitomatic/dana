"""Factory for creating I/O resources."""

from typing import Any

from .base_io import BaseIO
from .console_io import ConsoleIO
from .websocket_io import WebSocketIO


class IOFactory:
    """Creates and configures I/O resources."""

    @classmethod
    def create_io(cls, io_type: str | BaseIO = "console", config: dict[str, Any] | None = None) -> BaseIO:
        """Create IO resource instance.

        Args:
            io_type: Type of IO resource or existing resource instance
            config: Optional configuration for the resource

        Returns:
            Configured IO resource instance
        """
        if isinstance(io_type, BaseIO):
            return io_type

        config = config or {}
        io_type = io_type.lower()

        if io_type == "websocket":
            return WebSocketIO(**config)

        # Default to console
        return ConsoleIO(**config)
