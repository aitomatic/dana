from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dana.api.core.schemas import MessageCreate, ConversationCreate
from dana.api.core.schemas_v2 import (
    BaseMessage,
    HandlerMessage,
    HandlerConversation,
    AddChildNodeRequest,
    DeleteNodeRequest,
    UpdateNodeRequest,
)
from dana.api.repositories import AbstractConversationRepo, AbstractDomainKnowledgeRepo
from dana.api.core.database import get_db
from dana.api.core.schemas_v2 import KnowledgePackResponse
from dana.api.services.knowledge_pack.structuring_handler.orchestrator import KPStructuringOrchestrator
from dana.api.repositories import get_conversation_repo, get_domain_knowledge_repo
from ..ws.domain_knowledge_ws import kp_structuring_ws_notifier
from .common import KPConversationType
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{knowledge_id}/structure-gen-chat", response_model=KnowledgePackResponse)
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
    conversation = await conv_repo.get_conversation_by_kp_id_and_type(kp_id=knowledge_id, type=KPConversationType.STRUCTURING.value, db=db)
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
    handler = KPStructuringOrchestrator(
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


@router.delete("/{knowledge_id}/node")
async def delete_node(
    knowledge_id: int,
    request: DeleteNodeRequest,
    kb_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Delete a node from the knowledge pack tree.

    Args:
        knowledge_id: Knowledge pack ID
        request: Request containing topic_parts list
        kb_repo: Knowledge pack repository
        db: Database session

    Returns:
        Success message or error
    """
    try:
        # Validate knowledge pack exists
        kb = await kb_repo.get_kp(kp_id=knowledge_id, db=db)
        if kb is None:
            raise HTTPException(status_code=404, detail="Knowledge pack not found")

        # Delete the node from tree and corresponding folder
        await kb_repo.delete_kp_tree_node(kp_id=knowledge_id, topic_parts=request.topic_parts, db=db)

        return {"message": "Node deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting node for knowledge pack {knowledge_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{knowledge_id}/node")
async def update_tree_node(
    knowledge_id: int,
    request: UpdateNodeRequest,
    kb_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Update a node name in the knowledge pack tree.

    Args:
        knowledge_id: Knowledge pack ID
        request: Request containing topic_parts and node_name
        kb_repo: Knowledge pack repository
        db: Database session

    Returns:
        Success message or error
    """
    try:
        # Validate knowledge pack exists
        kb = await kb_repo.get_kp(kp_id=knowledge_id, db=db)
        if kb is None:
            raise HTTPException(status_code=404, detail="Knowledge pack not found")

        # Update the node name in tree and rename corresponding folder
        await kb_repo.update_kp_tree_node_name(kp_id=knowledge_id, topic_parts=request.topic_parts, node_name=request.node_name, db=db)

        return {"message": "Node updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating node for knowledge pack {knowledge_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{knowledge_id}/node/children")
async def add_child_node(
    knowledge_id: int,
    request: AddChildNodeRequest,
    kb_repo: type[AbstractDomainKnowledgeRepo] = Depends(get_domain_knowledge_repo),
    db: Session = Depends(get_db),
):
    """
    Add child nodes to a parent node in the knowledge pack tree.

    Args:
        knowledge_id: Knowledge pack ID
        request: Request containing topic_parts and child_topics
        kb_repo: Knowledge pack repository
        db: Database session

    Returns:
        Success message or error
    """
    try:
        # Validate knowledge pack exists
        kb = await kb_repo.get_kp(kp_id=knowledge_id, db=db)
        if kb is None:
            raise HTTPException(status_code=404, detail="Knowledge pack not found")

        # Add child nodes to the specified parent node
        await kb_repo.add_kp_tree_child_node(kp_id=knowledge_id, topic_parts=request.topic_parts, child_topics=request.child_topics, db=db)

        return {"message": "Child nodes added successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding child nodes for knowledge pack {knowledge_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
