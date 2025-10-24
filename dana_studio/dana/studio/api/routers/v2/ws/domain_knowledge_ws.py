from typing import Callable, Awaitable, override
from dana.studio.api.core.ws_manager import WSManager
from dana.studio.api.routers.v2.knowledge_pack.common import KPConversationType
import logging
import json
from datetime import datetime


logger = logging.getLogger(__name__)


class DomainKnowledgeWSManager(WSManager):
    WS_TYPE = "kp"

    def __init__(self, type: str, **kwargs):
        self.type = type

    @override
    def get_channel(self, *args, **kwargs):
        return str(self.WS_TYPE)

    @override
    def get_notifier(self, websocket_id: str) -> Callable[[dict], Awaitable[None]]:
        async def notifier(message: dict):
            """
            Message format :
                "tool_name": tool_name,
                "content": message,
                "status": status,
                "progression": progression,
                "path_parts": path_parts (optional),
            """
            if websocket_id:
                message_dict = {
                    "type": self.type,
                    "knowledge_id": websocket_id,
                    "message": message,
                    "timestamp": datetime.now().timestamp(),
                }
            await self.send_update_msg(websocket_id, json.dumps(message_dict))

        return notifier


# ALL OF THESE WILL HAVE THE SAME CHANNEL NAME, MULTIPLE INITIALIZATION JUST FOR CONVENIENCE
domain_knowledge_ws_notifier = DomainKnowledgeWSManager(type=KPConversationType.SMART_CHAT.value)
kp_structuring_ws_notifier = DomainKnowledgeWSManager(type=KPConversationType.STRUCTURING.value)
kp_question_generation_ws_notifier = DomainKnowledgeWSManager(type=KPConversationType.QUESTION_GENERATION.value)
kp_generation_ws_notifier = DomainKnowledgeWSManager(type=KPConversationType.KNOWLEDGE_GENERATION.value)
