from dana.api.core.schemas import IntentDetectionRequest, IntentDetectionResponse
from dana.api.services.intent_detection_service import IntentDetectionService
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource


class IntentDetectionService(IntentDetectionService):
    def __init__(self):
        super().__init__()
        self.llm = LegacyLLMResource()

    async def detect_intent(self, request: IntentDetectionRequest) -> IntentDetectionResponse:
        pass
