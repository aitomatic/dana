from dana.api.core.schemas import IntentDetectionRequest, IntentDetectionResponse
from dana.api.services.intent_detection_service import IntentDetectionService
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.common.types import BaseRequest
from dana.api.core.schemas import MessageData
from dana.api.services.intent_detection.intent_prompts import INTENT_DETECTION_PROMPT, DANA_ASSISTANT_PROMPT
from datetime import datetime, UTC
from dana.common.utils.misc import Misc
from dana.api.services.intent_detection.intent_handlers.knowledge_ops_handler import KnowledgeOpsHandler


class IntentDetectionService(IntentDetectionService):
    def __init__(self):
        super().__init__()
        self.llm = LLMResource()

    def _get_system_prompt(self):
        return DANA_ASSISTANT_PROMPT.format(current_date=datetime.now(UTC).strftime("%Y-%m-%d"))

    async def detect_intent(self, request: IntentDetectionRequest) -> IntentDetectionResponse:
        conversation = request.get_conversation_str(include_latest_user_message=True)

        prompt = INTENT_DETECTION_PROMPT.format(conversation=conversation)

        llm_request = BaseRequest(
            arguments={
                "messages": [{"role": "system", "content": self._get_system_prompt()}, {"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 500,
            }
        )

        response = await self.llm.query(llm_request)

        content = Misc.get_response_content(response)

        content_dict = Misc.text_to_dict(content)

        if content_dict.get("category") == "dana_code":
            pass
        elif content_dict.get("category") == "knowledge_ops":
            handler = KnowledgeOpsHandler(llm=self.llm, tree_structure=request.current_domain_tree)
            result = await handler.handle(request)
            return IntentDetectionResponse(
                intent=content_dict.get("category"),
                entities=result.get("entities", {}),
                explanation=result.get("message", ""),
                additional_data=result,
            )


if __name__ == "__main__":
    import asyncio

    service = IntentDetectionService()
    chat_history = []
    init = True
    while True:
        if init:
            user_message = "I want my agent to be an expert in semiconductor ion etching"
            init = False
        else:
            user_message = input("User: ")

        request = IntentDetectionRequest(user_message=user_message, chat_history=chat_history, current_domain_tree=None, agent_id=1)
        response = asyncio.run(service.detect_intent(request))
        chat_history.append(MessageData(role="user", content=user_message))
        chat_history.append(MessageData(role="assistant", content=response.intent))
        print(response.intent)
