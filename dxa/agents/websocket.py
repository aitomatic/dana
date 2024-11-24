"""WebSocket-based agent implementation."""

import asyncio
import json
import aiohttp
from typing import Dict, Optional, List
from datetime import datetime
from dxa.core.ooda_agent_with_experts import OODAAgentWithExperts
from dxa.perts.domain import DomainExpertLLM
from dxa.users.roles import User

class WebSocketModelUsingAgent(ooda_agent_with_experts):
    """WebSocket implementation of Model-Using OODA agent."""
    
    def __init__(
        self,
        agent_llm_config: Dict,
        domain_experts: List[DomainExpertLLM],
        users: List[User],
        websocket_url: str,
        session_id: str,
        agent_system_prompt: Optional[str] = None,
        heartbeat_interval: float = 30.0,  # Heartbeat every 30 seconds
        max_retries: int = 3,  # Maximum reconnection attempts
        retry_delay: float = 5.0  # Delay between retries in seconds
    ):
        """Initialize WebSocket-based agent."""
        super().__init__(agent_llm_config, domain_experts, users, agent_system_prompt)
        self.websocket_url = websocket_url
        self.session_id = session_id
        self.ws = None
        self._connected = False
        self._heartbeat_task = None
        self.heartbeat_interval = heartbeat_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def _heartbeat(self):
        """Send periodic heartbeat messages to keep connection alive."""
        while self._connected:
            try:
                await self._send_message({
                    "type": "heartbeat",
                    "timestamp": datetime.now().timestamp()
                })
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                self.logger.warning("Heartbeat failed: %s", str(e))
                if self._connected:  # Only try to reconnect if we haven't explicitly disconnected
                    await self._try_reconnect()

    async def _try_reconnect(self):
        """Attempt to reconnect to WebSocket server."""
        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    "Attempting to reconnect (attempt %d/%d)...",
                    attempt + 1,
                    self.max_retries
                )
                await self.connect()
                self.logger.info("Reconnection successful")
                return True
            except Exception as e:
                self.logger.error(
                    "Reconnection attempt %d failed: %s",
                    attempt + 1,
                    str(e)
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        self.logger.error("Failed to reconnect after %d attempts", self.max_retries)
        return False

    async def connect(self):
        """Establish WebSocket connection with retry logic."""
        if self._connected:
            return

        try:
            self.ws = await aiohttp.ClientSession().ws_connect(
                self.websocket_url,
                heartbeat=self.heartbeat_interval
            )
            self._connected = True
            self.logger.info("WebSocket connection established")
            
            # Start heartbeat task
            self._heartbeat_task = asyncio.create_task(self._heartbeat())
            
            # Send initial connection message
            await self._send_message({
                "type": "connect",
                "session_id": self.session_id,
                "agent_info": {
                    "experts": list(self.domain_experts.keys()),
                    "users": list(self.users.keys())
                }
            })
            
        except Exception as e:
            self.logger.error("WebSocket connection failed: %s", str(e))
            raise

    async def _send_message(self, data: Dict):
        """Send message through WebSocket with retry logic."""
        if not self._connected:
            if not await self._try_reconnect():
                raise ConnectionError("Not connected and reconnection failed")
        
        try:
            data['session_id'] = self.session_id
            data['timestamp'] = datetime.now().timestamp()
            await self.ws.send_json(data)
            
        except Exception as e:
            self.logger.error("Error sending WebSocket message: %s", str(e))
            self._connected = False
            if not await self._try_reconnect():
                raise

    async def _receive_message(self) -> Dict:
        """Receive message from WebSocket with retry logic."""
        if not self._connected:
            if not await self._try_reconnect():
                raise ConnectionError("Not connected and reconnection failed")
        
        try:
            msg = await self.ws.receive()
            
            if msg.type == aiohttp.WSMsgType.TEXT:
                return json.loads(msg.data)
            elif msg.type == aiohttp.WSMsgType.CLOSED:
                self.logger.warning("WebSocket connection closed")
                self._connected = False
                if await self._try_reconnect():
                    return await self._receive_message()
                raise ConnectionError("WebSocket closed and reconnection failed")
            elif msg.type == aiohttp.WSMsgType.ERROR:
                self.logger.error("WebSocket error: %s", str(msg.data))
                self._connected = False
                if await self._try_reconnect():
                    return await self._receive_message()
                raise ConnectionError(f"WebSocket error: {msg.data}")
                
        except Exception as e:
            self.logger.error("Error receiving WebSocket message: %s", str(e))
            self._connected = False
            if await self._try_reconnect():
                return await self._receive_message()
            raise

    async def disconnect(self):
        """Close WebSocket connection gracefully."""
        if self._connected and self.ws:
            try:
                # Cancel heartbeat task
                if self._heartbeat_task:
                    self._heartbeat_task.cancel()
                    try:
                        await self._heartbeat_task
                    except asyncio.CancelledError:
                        pass
                
                # Send disconnect message
                await self._send_message({
                    "type": "disconnect",
                    "message": "Agent disconnecting"
                })
                
                # Close connection
                await self.ws.close()
                
            except Exception as e:
                self.logger.error("Error during disconnect: %s", str(e))
            finally:
                self._connected = False
                self.logger.info("WebSocket connection closed")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
