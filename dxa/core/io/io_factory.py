"""
IO Factory
"""

from typing import Union
from .base_io import BaseIO
from .console_io import ConsoleIO
from .websocket_io import WebSocketIO

class IOFactory:
    """Creates and configures IO systems."""
    
    @classmethod
    def create_io(cls, io_type: Union[str, BaseIO] = "console") -> BaseIO:
        """Create IO instance."""
        if isinstance(io_type, BaseIO):
            return io_type
        io_type = io_type or "console"
        if io_type == "websocket":
            return WebSocketIO(url="ws://localhost:8000")
        if io_type == "console":
            return ConsoleIO()
        return ConsoleIO()
