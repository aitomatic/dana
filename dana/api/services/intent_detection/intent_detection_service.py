from dana.api.services.intent_detection_service import IntentDetectionService
from dana.common.resource.llm.llm_resource import LLMResource
from dana.common.types import BaseRequest
from dana.api.core.schemas import IntentDetectionRequest, IntentDetectionResponse, DomainKnowledgeTree, MessageData


class IntentDetectionService(IntentDetectionService):
    def __init__(self):
        super().__init__()
        self.llm = LLMResource()

    async def detect_intent(self, request: IntentDetectionRequest) -> IntentDetectionResponse:
        pass
