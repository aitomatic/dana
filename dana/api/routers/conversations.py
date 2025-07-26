"""
Conversation routers - routing for conversation management endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dana.api.core.database import get_db
from dana.api.core.schemas import ConversationCreate, ConversationRead, ConversationWithMessages, MessageCreate, MessageRead
from dana.api.services.conversation_service import get_conversation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationRead)
async def create_conversation(
    request: ConversationCreate, db: Session = Depends(get_db), conversation_service=Depends(get_conversation_service)
):
    """Create a new conversation."""
    try:
        conversation = await conversation_service.create_conversation(request, db)
        return conversation

    except Exception as e:
        logger.error(f"Error in create conversation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    include_messages: bool = True,
    db: Session = Depends(get_db),
    conversation_service=Depends(get_conversation_service),
):
    """Get a conversation by ID."""
    try:
        conversation = await conversation_service.get_conversation(conversation_id, db, include_messages)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get conversation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[ConversationRead])
async def list_conversations(
    agent_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    conversation_service=Depends(get_conversation_service),
):
    """List conversations with optional filtering."""
    try:
        conversations = await conversation_service.list_conversations(agent_id=agent_id, limit=limit, offset=offset, db_session=db)
        return conversations

    except Exception as e:
        logger.error(f"Error in list conversations endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    conversation_id: int, request: ConversationCreate, db: Session = Depends(get_db), conversation_service=Depends(get_conversation_service)
):
    """Update a conversation."""
    try:
        conversation = await conversation_service.update_conversation(conversation_id, request, db)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update conversation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int, db: Session = Depends(get_db), conversation_service=Depends(get_conversation_service)):
    """Delete a conversation."""
    try:
        success = await conversation_service.delete_conversation(conversation_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete conversation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Message endpoints
@router.post("/{conversation_id}/messages/", response_model=MessageRead)
async def create_message(
    conversation_id: int, request: MessageCreate, db: Session = Depends(get_db), conversation_service=Depends(get_conversation_service)
):
    """Create a new message in a conversation."""
    try:
        message = await conversation_service.create_message(conversation_id, request, db)
        return message

    except Exception as e:
        logger.error(f"Error in create message endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/messages/", response_model=list[MessageRead])
async def list_messages(
    conversation_id: int,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    conversation_service=Depends(get_conversation_service),
):
    """List messages in a conversation."""
    try:
        messages = await conversation_service.list_messages(conversation_id, limit, offset, db)
        return messages

    except Exception as e:
        logger.error(f"Error in list messages endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/messages/{message_id}", response_model=MessageRead)
async def get_message(
    conversation_id: int, message_id: int, db: Session = Depends(get_db), conversation_service=Depends(get_conversation_service)
):
    """Get a specific message in a conversation."""
    try:
        message = await conversation_service.get_message(conversation_id, message_id, db)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return message

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get message endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{conversation_id}/messages/{message_id}", response_model=MessageRead)
async def update_message(
    conversation_id: int,
    message_id: int,
    request: MessageCreate,
    db: Session = Depends(get_db),
    conversation_service=Depends(get_conversation_service),
):
    """Update a message in a conversation."""
    try:
        message = await conversation_service.update_message(conversation_id, message_id, request, db)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return message

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update message endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}/messages/{message_id}")
async def delete_message(
    conversation_id: int, message_id: int, db: Session = Depends(get_db), conversation_service=Depends(get_conversation_service)
):
    """Delete a message from a conversation."""
    try:
        success = await conversation_service.delete_message(conversation_id, message_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="Message not found")
        return {"message": "Message deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete message endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
