from fastapi import WebSocket
import asyncio
from typing import Any, Literal, Callable, Coroutine
from dana.api.core.bc_engine import WsBroadcastEngine
import logging

logger = logging.getLogger(__name__)


class DomainKnowledgeWSNotifier:
    def __init__(self, type: str):
        self.type = type

    async def connect(self, websocket_id: str, session_id: str, websocket: WebSocket):
        await websocket.accept()

    def disconnect(self, websocket_id: str, session_id: str):
        pass

    def get_channel(self, websocket_id: str):
        return f"chatroom_{websocket_id}"

    async def run_ws_loop_forever(self, websocket: WebSocket, websocket_id: str):
        channel = self.get_channel(websocket_id)
        # Broadcast to all connections with this channel
        await WsBroadcastEngine.run_broadcast_loop_forever(websocket, channel)

    async def send_update_msg(
        self,
        websocket_id: Any,
        message: str,
    ):
        """Send a message via WebSocket"""

        await WsBroadcastEngine.broadcast_message(channel=self.get_channel(websocket_id), message=message)


domain_knowledge_ws_notifier = DomainKnowledgeWSNotifier(type="domain_knowledge_update")


def create_domain_knowledge_ws_notifier(
    websocket_id: str | None = None,
) -> Coroutine[Any, Any, Callable[[str, str, str, float | None], None]]:
    """Create a chat update notifier that sends updates via WebSocket"""

    async def domain_knowledge_update_notifier(
        tool_name: str, message: str, status: Literal["init", "in_progress", "finish", "error"], progression: float | None = None
    ) -> None:
        # Send via WebSocket if connection exists
        if websocket_id:
            message_dict = {
                "type": domain_knowledge_ws_notifier.type,
                "message": {
                    "tool_name": tool_name,
                    "content": message,
                    "status": status,
                    "progression": progression,
                },
                "timestamp": asyncio.get_event_loop().time(),
            }
            import json

            await domain_knowledge_ws_notifier.send_update_msg(websocket_id, json.dumps(message_dict))

    return domain_knowledge_update_notifier
