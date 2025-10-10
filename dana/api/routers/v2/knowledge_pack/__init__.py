"""
Domain Knowledge routers - API endpoints for managing agent domain knowledge trees.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.schemas import (
    KnowledgePackCreateRequest,
    KnowledgePackUpdateRequest,
    KnowledgePackOutput,
    ConversationCreate,
    MessageCreate,
    MessageData,
    IntentDetectionRequest,
    KnowledgePackSmartChatResponse,
    PaginatedKnowledgePackResponse,
)
from dana.api.core.schemas_v2 import BaseMessage, DomainKnowledgeTreeV2
from dana.api.repositories import get_domain_knowledge_repo, AbstractDomainKnowledgeRepo, get_conversation_repo, AbstractConversationRepo
from dana.api.services.intent_detection.intent_handlers.knowledge_ops_handler import KnowledgeOpsHandler
from ..ws.domain_knowledge_ws import domain_knowledge_ws_notifier
from fastapi import WebSocket
from fastapi.concurrency import run_until_first_complete
from .kp_structuring import router as kp_structuring_router
from .common import KPConversationType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge-pack"])
router.include_router(kp_structuring_router)


@router.get("/{knowledge_id}", response_model=DomainKnowledgeTreeV2 | dict)
async def get_knowledge_pack(
    knowledge_id: int, repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo), db: Session = Depends(get_db)
):
    """
    Get the current domain knowledge tree for a knowledge.
    """
    try:
        tree = await repo.get_kp_tree(kp_id=knowledge_id)
        return tree
    except Exception as e:
        logger.error(f"Error getting knowledge pack {knowledge_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=PaginatedKnowledgePackResponse)
async def list_knowledge_packs(
    limit: int = 100,
    offset: int = 0,
    repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    List all knowledge packs with optional filtering.
    """
    return await repo.list_kp(limit=limit, offset=offset, db=db)


@router.post("/create", response_model=KnowledgePackOutput)
async def create_knowledge_pack(
    request: KnowledgePackCreateRequest,
    repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Initialize a knowledge pack.
    """
    try:
        metadata = request.kp_metadata.model_dump()
        kp = await repo.create_kp(kp_metadata=metadata, db=db)
        return kp
    except Exception as e:
        logger.error(f"Error creating knowledge pack: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update", response_model=KnowledgePackOutput)
async def update_knowledge_pack(
    request: KnowledgePackUpdateRequest,
    repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Initialize a knowledge pack.
    """
    try:
        metadata = request.kp_metadata.model_dump()
        return await repo.update_kp(kp_id=request.kp_id, kp_metadata=metadata, db=db)
    except ValueError as e:
        logger.error(f"Bad request error updating knowledge pack: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error updating knowledge pack: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{knowledge_id}/smart-chat", response_model=KnowledgePackSmartChatResponse)
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
    conversation = await conv_repo.get_conversation_by_kp_id_and_type(kp_id=knowledge_id, type=KPConversationType.SMART_CHAT.value, db=db)
    if not conversation:
        conversation = await conv_repo.create_conversation(
            conversation_data=ConversationCreate(title=f"Generate knowledge pack [{knowledge_id}]", agent_id=None, kp_id=knowledge_id),
            messages=[request],
            type=KPConversationType.SMART_CHAT.value,
            db=db,
        )
    else:
        conversation = await conv_repo.add_messages_to_conversation(conversation_id=conversation.id, messages=[request], db=db)

    kb = await kb_repo.get_kp(kp_id=knowledge_id, db=db)
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge pack not found")
    spec = kb.get_specialization_info()

    intent_request = IntentDetectionRequest(
        user_message=request.content,
        chat_history=[
            MessageData(
                role=message.sender, content=message.content, require_user=message.require_user, treat_as_tool=message.treat_as_tool
            )
            for message in conversation.messages
        ],
        current_domain_tree=await kb_repo.get_kp_tree(kp_id=knowledge_id, db=db),
        agent_id=knowledge_id,
    )
    handler = KnowledgeOpsHandler(
        domain_knowledge_path=str(kb_repo.get_knowledge_tree_path(knowledge_id).absolute()),
        domain=spec.domain,
        role=spec.role,
        tasks=[spec.task],
        notifier=domain_knowledge_ws_notifier.get_notifier(websocket_id=str(knowledge_id)),
    )
    logger.info(f"🚀 Starting KnowledgeOpsHandler workflow for knowledge pack {knowledge_id}")
    result = await handler.handle(intent_request)
    logger.info(f"✅ KnowledgeOpsHandler completed for knowledge pack {knowledge_id}: status={result.get('status')}")
    new_messages = []
    internal_conversation = result.get("conversation", [])
    for message in reversed(internal_conversation):
        if (
            conversation.messages
            and message.role == conversation.messages[-1].sender
            and message.content == conversation.messages[-1].content
        ):
            break
        new_messages.append(
            MessageCreate(
                sender=message.role,
                content=message.content,
                require_user=message.require_user,
                treat_as_tool=message.treat_as_tool,
            )
        )
    new_messages = new_messages[::-1]
    # Update new messages to conversation
    await conv_repo.add_messages_to_conversation(conversation_id=conversation.id, messages=new_messages, db=db)

    return KnowledgePackSmartChatResponse(
        success=True,
        is_tree_modified=result.get("tree_modified", False),
        agent_response=result.get("message", "Knowledge operation completed successfully."),
        internal_conversation=internal_conversation[-len(new_messages) :],
        error=result.get("error", None),
    )


@router.websocket("/ws/{knowledge_id}")
async def send_chat_update_msg(knowledge_id: str, websocket: WebSocket):
    await run_until_first_complete(
        (domain_knowledge_ws_notifier.run_ws_loop_forever, {"websocket": websocket, "websocket_id": knowledge_id}),
    )


@router.get("/test-ws/{knowledge_id}")
async def test_ws(knowledge_id: str, message: str):
    await domain_knowledge_ws_notifier.send_update_msg(knowledge_id, message)
