import asyncio
from typing import Literal, Callable, Awaitable, override
from dana.lang.api.core.ws_manager import WSManager
from dana.lang.api.routers.v2.knowledge_pack.common import KPConversationType
import logging
import json


logger = logging.getLogger(__name__)


class DomainKnowledgeWSManager(WSManager):
    WS_TYPE = "kp"

    def __init__(self, prefix: str, **kwargs):
        self.prefix = prefix

    @override
    def get_channel(self, *args, **kwargs):
        return str(self.WS_TYPE)

    @override
    def get_notifier(
        self, websocket_id: str
    ) -> Callable[[str, str, Literal["init", "in_progress", "finish", "error"], float | None], Awaitable[None]]:
        async def notifier(
            tool_name: str, message: str, status: Literal["init", "in_progress", "finish", "error"], progression: float | None = None
        ):
            if websocket_id:
                message_dict = {
                    "type": self.prefix,
                    "knowledge_id": websocket_id,
                    "message": {
                        "tool_name": tool_name,
                        "content": message,
                        "status": status,
                        "progression": progression,
                    },
                    "timestamp": asyncio.get_event_loop().time(),
                }
            await self.send_update_msg(websocket_id, json.dumps(message_dict))

        return notifier


domain_knowledge_ws_notifier = DomainKnowledgeWSManager(prefix=KPConversationType.SMART_CHAT.value)
kp_structuring_ws_notifier = DomainKnowledgeWSManager(prefix=KPConversationType.STRUCTURING.value)
kp_question_generation_ws_notifier = DomainKnowledgeWSManager(prefix=KPConversationType.QUESTION_GENERATION.value)
kp_generation_ws_notifier = DomainKnowledgeWSManager(prefix=KPConversationType.KNOWLEDGE_GENERATION.value)
