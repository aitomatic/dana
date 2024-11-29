"""I/O implementations for DXA.

This package provides various I/O implementations for DXA, including:
- ConsoleIO: For console-based input/output
- WebSocketIO: For WebSocket-based real-time communication

Example:
    ```python
    from dxa.core.io import ConsoleIO, WebSocketIO
    
    # Using console I/O
    async with ConsoleIO() as io:
        await io.send_message("Hello!")
        
    # Using WebSocket I/O
    async with WebSocketIO("ws://localhost:8765") as io:
        await io.send_message("Hello!")
    ```
"""

from dxa.core.io.console_io import ConsoleIO
from dxa.core.io.websocket_io import WebSocketIO

__all__ = ['ConsoleIO', 'WebSocketIO'] 