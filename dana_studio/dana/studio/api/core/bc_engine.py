from fastapi import WebSocket
from broadcaster import Broadcast
from starlette.websockets import WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)

broadcast_engine = Broadcast("memory://")  # NOTE : Change this to


class WsBroadcastEngine:
    @staticmethod
    async def run_broadcast_loop_forever(websocket: WebSocket, channel: str):
        """
        Loop that receive message from the broadcast engine and broadcast to the websocket
        """
        try:
            async with broadcast_engine.subscribe(channel=channel) as subscriber:
                async for event in subscriber:
                    await websocket.send_text(event.message)
        except WebSocketDisconnect as e:
            logger.info(f"WebSocket disconnected on channel '{channel}' with code: {e.code}")
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket broadcast loop for channel '{channel}': {e}")

    @staticmethod
    async def broadcast_message(
        channel: str,
        message: str,
    ):
        """
        Send a message to broadcast engine
        """

        await broadcast_engine.publish(channel=channel, message=message)
