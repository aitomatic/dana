"""I/O resource implementations for Dana.

This package provides various I/O resource implementations, including:
- ConsoleIO: For console-based input/output
- WebSocketIO: For WebSocket-based real-time communication

Example:
    ```python
    from dana.common.io import ConsoleIO, WebSocketIO

    # Using console I/O
    async with ConsoleIO() as io:
        await io.send("Hello!")

    # Using WebSocket I/O
    async with WebSocketIO("ws://localhost:8765") as io:
        await io.send("Hello!")
    ```
"""

from dana.common.io.base_io import BaseIO
from dana.common.io.console_io import ConsoleIO
from dana.common.io.io_factory import IOFactory
from dana.common.io.websocket_io import WebSocketIO

__all__ = ["BaseIO", "ConsoleIO", "WebSocketIO", "IOFactory"]
