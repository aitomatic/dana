"""I/O resource implementations for DXA.

This package provides various I/O resource implementations, including:
- ConsoleIOResource: For console-based input/output
- WebSocketIOResource: For WebSocket-based real-time communication

Example:
    ```python
    from dxa.core.io import ConsoleIOResource, WebSocketIOResource

    # Using console I/O
    async with ConsoleIOResource() as io:
        await io.send("Hello!")

    # Using WebSocket I/O
    async with WebSocketIOResource("ws://localhost:8765") as io:
        await io.send("Hello!")
    ```
"""

from .base_io import BaseIO
from .console_io import ConsoleIO
from .websocket_io import WebSocketIO
from .io_factory import IOFactory

__all__ = [
    'BaseIO',
    'ConsoleIO',
    'WebSocketIO',
    'IOFactory'
]
