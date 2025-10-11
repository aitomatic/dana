from fastapi import WebSocket
import asyncio
from typing import Any, Callable
from .bc_engine import WsBroadcastEngine
import logging
import json


logger = logging.getLogger(__name__)


class WSManager:
    WS_TYPE = "DEFAULT"

    def __init__(self, **kwargs):
        self.prefix = kwargs.get("prefix", "chatroom")

    def get_channel(self, websocket_id: str):
        return f"{self.WS_TYPE}.{self.prefix}_{websocket_id}"

    async def run_ws_loop_forever(self, websocket: WebSocket, websocket_id: str):
        """
        Loop that receive message from the broadcast engine and broadcast to the websocket
        """
        channel = self.get_channel(websocket_id)
        await WsBroadcastEngine.run_broadcast_loop_forever(websocket, channel)

    async def send_update_msg(
        self,
        websocket_id: Any,
        message: str,
    ):
        """
        Send a message to broadcast engine. Then this message will be broadcast to all connections in this channel
        """

        await WsBroadcastEngine.broadcast_message(channel=self.get_channel(websocket_id), message=message)

    def get_notifier(self, websocket_id: str) -> Callable:
        """
        Default notifier which is a callable that sends a message to the broadcast engine
        """

        async def notifier(message: str):
            if websocket_id:
                message_dict = {
                    "type": self.WS_TYPE,
                    "message": message,
                    "timestamp": asyncio.get_event_loop().time(),
                }
            await self.send_update_msg(websocket_id, json.dumps(message_dict))

        return notifier
