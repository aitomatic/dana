"""WebSocket I/O implementation for DXA.

This module provides a WebSocket-based implementation of the BaseIO interface,
enabling real-time bidirectional communication over WebSocket connections.

Example:
    ```python
    async with WebSocketIO("ws://localhost:8765") as ws:
        await ws.send_message("Hello, WebSocket!")
        response = await ws.get_input()
    ```
"""

from typing import Optional, Any
import asyncio
from urllib.parse import urlparse
from websockets.legacy.server import WebSocketServerProtocol as WebSocket
from websockets import serve
from dxa.core.io.base_io import BaseIO

class WebSocketIO(BaseIO):
    """WebSocket-based I/O implementation.
    
    This class implements the BaseIO interface using WebSocket connections,
    providing real-time bidirectional communication capabilities.

    Args:
        url: The WebSocket URL to connect to (e.g., "ws://localhost:8765")
        max_retries: Maximum number of connection retry attempts
        retry_delay: Delay in seconds between retry attempts

    Attributes:
        host: The WebSocket server hostname
        port: The WebSocket server port
        max_retries: Maximum number of connection retry attempts
        retry_delay: Delay between retry attempts
        _server: The WebSocket server instance
        _current_connection: The current active WebSocket connection
        _message_queue: Queue for handling incoming messages
    """
    
    def __init__(self, url: str, max_retries: int = 3, retry_delay: float = 1.0):
        super().__init__()
        parsed = urlparse(url)
        self.host = parsed.hostname or 'localhost'
        self.port = parsed.port or 8765
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._server: Optional[WebSocket] = None
        self._current_connection: Optional[WebSocket] = None
        self._message_queue: asyncio.Queue[str] = asyncio.Queue()
    
    async def _handle_connection(self, websocket: WebSocket) -> None:
        """Handle incoming WebSocket connection."""
        self._current_connection = websocket
        try:
            async for message in websocket:
                await self._message_queue.put(message)
        finally:
            self._current_connection = None
    
    async def initialize(self) -> None:
        """Initialize WebSocket server."""
        self._server = await serve(self._handle_connection, self.host, self.port)
    
    async def cleanup(self) -> None:
        """Cleanup WebSocket."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
    
    async def send(self, message: Any) -> None:
        """Send through WebSocket."""
        if self._current_connection and self._current_connection.open:
            await self._current_connection.send(message)
    
    async def receive(self) -> Any:
        """Receive from WebSocket."""
        return await self._message_queue.get()
  