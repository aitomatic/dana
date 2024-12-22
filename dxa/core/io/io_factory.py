"""
IO Factory
"""

from .base_io import BaseIO
from .console_io import ConsoleIO
from .websocket_io import WebSocketIO
from typing import Union

class IOFactory:
    """Creates and configures IO systems."""
    
    @classmethod
    def create_io(cls, io_type: Union[str, BaseIO] = None) -> BaseIO:
        """Create IO instance."""
        if isinstance(io_type, BaseIO):
            return io_type
        io_type = io_type or "console"
        if io_type == "websocket":
            return WebSocketIO()
        if io_type == "console":
            return ConsoleIO()
        return BaseIO()
