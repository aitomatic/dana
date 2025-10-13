"""WebSocket I/O resource implementation for Dana.

This module provides a WebSocket-based implementation of the BaseIOResource interface,
enabling real-time bidirectional communication over WebSocket connections.
"""

import asyncio
from typing import Any
from urllib.parse import urlparse

from websockets import serve
from websockets.asyncio.server import Server
from websockets.legacy.server import WebSocketServerProtocol

from .base_io import BaseIO


class WebSocketIO(BaseIO):
    """WebSocket-based I/O resource implementation."""

    def __init__(
        self,
        url: str = "ws://localhost:8765",
        name: str = "websocket",
        description: str | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize WebSocket I/O resource."""
        super().__init__(name, description or "WebSocket-based I/O resource")
        parsed = urlparse(url)
        self.host = parsed.hostname or "localhost"
        self.port = parsed.port or 8765
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._server: Server | None = None
        self._current_connection: WebSocketServerProtocol | None = None
        self._message_queue: asyncio.Queue[str] = asyncio.Queue()

    async def _handle_connection(self, websocket: WebSocketServerProtocol) -> None:
        """Handle incoming WebSocket connection."""
        self._current_connection = websocket
        try:
            async for message in websocket:
                # Handle both string and bytes messages
                str_message = message.decode() if isinstance(message, bytes) else str(message)
                await self._message_queue.put(str_message)
        finally:
            if self._current_connection is websocket:
                self._current_connection = None

    async def initialize(self) -> None:
        """Initialize WebSocket server."""
        await super().initialize()
        # Use typing.cast to handle the type mismatch between websockets and the expected handler signature
        from typing import Any, cast

        handler = cast(Any, self._handle_connection)
        self._server = await serve(handler, self.host, self.port)
        self.info(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def cleanup(self) -> None:
        """Cleanup WebSocket connections."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        await super().cleanup()
        self.info("WebSocket server shut down")

    async def send(self, message: Any) -> None:
        """Send message through WebSocket."""
        if self._current_connection and not self._current_connection.closed:
            await self._current_connection.send(str(message))
        else:
            self.warning("No active WebSocket connection for sending message")

    async def receive(self) -> Any:
        """Receive message from WebSocket."""
        return await self._message_queue.get()
