from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dana.api.core.schemas import MessageCreate, ConversationCreate
from dana.api.core.schemas_v2 import BaseMessage, HandlerMessage, HandlerConversation
from dana.api.repositories import AbstractConversationRepo, AbstractDomainKnowledgeRepo
from dana.api.core.database import get_db
from dana.api.core.schemas_v2 import KnowledgePackResponse
from dana.api.services.knowledge_pack.question_handler.orchestrator import KPQuestionGenerationOrchestrator
from dana.api.repositories import get_conversation_repo, get_domain_knowledge_repo
from ..ws.domain_knowledge_ws import kp_structuring_ws_notifier
from .common import KPConversationType
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{knowledge_id}/question-gen-chat", response_model=KnowledgePackResponse)
async def smart_chat(
    knowledge_id: int,
    request: BaseMessage,
    conv_repo: type[AbstractConversationRepo] = Depends(get_conversation_repo),
    kb_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    # API for compatibility with smart_chat_v2.py
    Smart chat for a knowledge pack.
    """
    conversation = await conv_repo.get_conversation_by_kp_id_and_type(
        kp_id=knowledge_id, type=KPConversationType.QUESTION_GENERATION.value, db=db
    )
    if not conversation:
        conversation = await conv_repo.create_conversation(
            conversation_data=ConversationCreate(title=f"Generate knowledge pack [{knowledge_id}]", agent_id=None, kp_id=knowledge_id),
            messages=[request],
            type=KPConversationType.STRUCTURING.value,
            db=db,
        )
    else:
        conversation = await conv_repo.add_messages_to_conversation(conversation_id=conversation.id, messages=[request], db=db)

    kb = await kb_repo.get_kp(kp_id=knowledge_id, db=db)
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge pack not found")
    spec = kb.get_specialization_info()

    intent_request = HandlerConversation(
        messages=[
            HandlerMessage(
                role=message.sender, content=message.content, require_user=message.require_user, treat_as_tool=message.treat_as_tool
            )
            for message in conversation.messages
        ],
    )
    handler = KPQuestionGenerationOrchestrator(
        domain_knowledge_path=str(kb_repo.get_knowledge_tree_path(knowledge_id).absolute()),
        domain=spec.domain,
        role=spec.role,
        tasks=[spec.task],
        notifier=kp_structuring_ws_notifier.get_notifier(websocket_id=str(knowledge_id)),
    )
    logger.info(f"🚀 Starting KnowledgeOpsHandler workflow for knowledge pack {knowledge_id}")
    result = await handler.handle(intent_request)
    logger.info(f"✅ KnowledgeOpsHandler completed for knowledge pack {knowledge_id}: status={result.get('status')}")
    new_messages = []
    internal_conversation = result.get("conversation", [])
    for message in reversed(internal_conversation):
        if (
            conversation.messages
            and message.sender == conversation.messages[-1].sender
            and message.content == conversation.messages[-1].content
        ):
            break
        new_messages.append(
            MessageCreate(
                sender=message.sender,
                content=message.content,
                require_user=message.require_user,
                treat_as_tool=message.treat_as_tool,
            )
        )
    new_messages = new_messages[::-1]
    # Update new messages to conversation
    await conv_repo.add_messages_to_conversation(conversation_id=conversation.id, messages=new_messages, db=db)

    return KnowledgePackResponse(
        success=True,
        is_tree_modified=result.get("tree_modified", False),
        agent_response=result.get("message", "Knowledge operation completed successfully."),
        internal_conversation=internal_conversation[-len(new_messages) :],
        error=result.get("error", None),
    )
