from fastapi import WebSocket
from broadcaster import Broadcast
import logging

logger = logging.getLogger(__name__)

broadcast_engine = Broadcast("memory://")  # NOTE : Change this to


class WsBroadcastEngine:
    @staticmethod
    async def run_broadcast_loop_forever(websocket: WebSocket, channel: str):
        async with broadcast_engine.subscribe(channel=channel) as subscriber:
            async for event in subscriber:
                await websocket.send_text(event.message)

    @staticmethod
    async def broadcast_message(
        channel: str,
        message: str,
    ):
        """Send a message via WebSocket"""

        await broadcast_engine.publish(channel=channel, message=message)
