"""I/O resource implementations for DXA.

This package provides various I/O resource implementations, including:
- ConsoleIO: For console-based input/output
- WebSocketIO: For WebSocket-based real-time communication

Example:
    ```python
    from opendxa.common.io import ConsoleIO, WebSocketIO

    # Using console I/O
    async with ConsoleIO() as io:
        await io.send("Hello!")

    # Using WebSocket I/O
    async with WebSocketIO("ws://localhost:8765") as io:
        await io.send("Hello!")
    ```
"""

from opendxa.common.io.base_io import BaseIO
from opendxa.common.io.console_io import ConsoleIO
from opendxa.common.io.websocket_io import WebSocketIO
from opendxa.common.io.io_factory import IOFactory

__all__ = [
    'BaseIO',
    'ConsoleIO',
    'WebSocketIO',
    'IOFactory'
]
