from fastapi import WebSocket
import json
import asyncio
from typing import Any, Literal, Callable, Coroutine
import logging

logger = logging.getLogger(__name__)


class DomainKnowledgeWSNotifier:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket_id] = websocket

    def disconnect(self, websocket_id: str):
        try:
            if websocket_id in self.active_connections:
                del self.active_connections[websocket_id]
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket {websocket_id}: {e}")

    async def send_chat_update_msg(
        self,
        websocket_id: Any,
        tool_name: str,
        message: str,
        status: Literal["init", "in_progress", "finish", "error"],
        progression: float | None = None,
    ):
        """Send a message via WebSocket"""
        if not isinstance(websocket_id, str):
            websocket_id = str(websocket_id)
        if websocket_id in self.active_connections:
            websocket = self.active_connections[websocket_id]
            try:
                message_dict = {
                    "type": "domain_knowledge_update",
                    "message": {
                        "tool_name": tool_name,
                        "content": message,
                        "status": status,
                        "progression": progression,
                    },
                    "timestamp": asyncio.get_event_loop().time(),
                }
                await websocket.send_text(json.dumps(message_dict))
            except Exception as e:
                logger.error(f"Failed to send chat update message via WebSocket: {e}")
                # Remove disconnected WebSocket
                self.disconnect(websocket_id)


domain_knowledge_ws_notifier = DomainKnowledgeWSNotifier()


def create_domain_knowledge_ws_notifier(
    websocket_id: str | None = None,
) -> Coroutine[Any, Any, Callable[[str, str, str, float | None], None]]:
    """Create a chat update notifier that sends updates via WebSocket"""

    async def domain_knowledge_update_notifier(
        tool_name: str, message: str, status: Literal["init", "in_progress", "finish", "error"], progression: float | None = None
    ) -> None:
        # Send via WebSocket if connection exists
        if websocket_id:
            await domain_knowledge_ws_notifier.send_chat_update_msg(websocket_id, tool_name, message, status, progression)

    return domain_knowledge_update_notifier
