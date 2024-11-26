"""WebSocket I/O implementation."""

from typing import Optional
import asyncio
from aiohttp import (
    ClientSession,
    ClientWebSocketResponse,
    WSMsgType
)
from dxa.core.io.base_io import BaseIO

class WebSocketError(Exception):
    """WebSocket-specific errors."""
    pass

class WebSocketIO(BaseIO):
    """WebSocket-based I/O implementation."""
    
    def __init__(
        self,
        websocket_url: str,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 1.0
    ):
        """Initialize WebSocket I/O."""
        super().__init__()
        self.websocket_url = websocket_url
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.ws: Optional[ClientWebSocketResponse] = None
        self.session: Optional[ClientSession] = None
        self._connected = False
        self._heartbeat_task = None

    async def send_message(self, message: str) -> None:
        """Send a message through WebSocket."""
        if not self._connected:
            await self._ensure_connection()
            
        try:
            await self.ws.send_json({
                "type": "message",
                "content": message,
                "timestamp": asyncio.get_event_loop().time()
            })
            # Track outgoing message
            self.state_manager.add_message(
                content=message,
                sender="system",
                receiver="websocket"
            )
        except Exception as e:
            self.state_manager.add_observation(
                content=f"Send error: {str(e)}",
                source="websocket_io",
                metadata={"error_type": "send_failed"}
            )
            await self._handle_connection_error(e)
        
    async def get_input(self, prompt: Optional[str] = None) -> str:
        """Get input through WebSocket."""
        if not self._connected:
            await self._ensure_connection()
            
        if prompt:
            await self.send_message(prompt)
            
        try:
            while True:  # Keep trying until we get valid input
                msg = await self.ws.receive()
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = msg.json()
                        if data.get("type") == "input":
                            response = data["content"].strip()
                            # Track incoming message
                            self.state_manager.add_message(
                                content=response,
                                sender="websocket",
                                receiver="system"
                            )
                            return response
                    except ValueError:
                        continue  # Not JSON or wrong format
                elif msg.type == WSMsgType.CLOSED:
                    raise WebSocketError("Connection closed")
                elif msg.type == WSMsgType.ERROR:
                    raise WebSocketError(f"WebSocket error: {str(msg.data)}")
                
        except Exception as e:
            self.state_manager.add_observation(
                content=f"Receive error: {str(e)}",
                source="websocket_io",
                metadata={"error_type": "receive_failed"}
            )
            await self._handle_connection_error(e)
            raise

    async def _handle_connection_error(self, error: Exception) -> None:
        """Handle connection errors with potential reconnection."""
        self._connected = False
        self.logger.error("WebSocket error: %s", str(error))
        
        try:
            await self._ensure_connection()
        except WebSocketError as e:
            self.logger.error("Failed to reconnect: %s", str(e))
            raise

    async def _ensure_connection(self) -> None:
        """Ensure WebSocket connection is active."""
        if not self._connected:
            for attempt in range(self.reconnect_attempts):
                try:
                    await self.initialize()
                    return
                except Exception as e:
                    if attempt == self.reconnect_attempts - 1:
                        raise WebSocketError(
                            f"Failed to reconnect after {self.reconnect_attempts} "
                            f"attempts: {str(e)}"
                        )
                    delay = self.reconnect_delay * (attempt + 1)
                    self.logger.warning(
                        "Reconnection attempt %d failed, waiting %.1fs: %s",
                        attempt + 1,
                        delay,
                        str(e)
                    )
                    await asyncio.sleep(delay)

    async def _start_heartbeat(self):
        """Start heartbeat task."""
        while self._connected:
            try:
                await self.ws.ping()
                await asyncio.sleep(20)  # Heartbeat every 20 seconds
            except Exception as e:
                self.logger.warning("Heartbeat failed: %s", str(e))
                await self._handle_connection_error(e)
                break

    async def initialize(self) -> None:
        """Initialize WebSocket connection."""
        try:
            if self.session is None:
                self.session = ClientSession()
            self.ws = await self.session.ws_connect(
                self.websocket_url,
                heartbeat=20.0,
                autoclose=True,
                autoping=True
            )
            self._connected = True
            
            # Start heartbeat task
            if self._heartbeat_task is None:
                self._heartbeat_task = asyncio.create_task(self._start_heartbeat())
                
        except Exception as e:
            self._connected = False
            if self.session:
                await self.session.close()
                self.session = None
            raise WebSocketError(f"Failed to initialize WebSocket: {str(e)}")

    async def cleanup(self) -> None:
        """Clean up WebSocket connection."""
        try:
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
                self._heartbeat_task = None
                
            if self.ws:
                await self.ws.close()
            if self.session:
                await self.session.close()
        finally:
            self.ws = None
            self.session = None
            self._connected = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup() 