from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import db, schemas
from ..services import ChatService, ConversationService, MessageService, get_agent

router = APIRouter(prefix="/chat", tags=["chat"])

def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

def get_chat_service():
    conversation_service = ConversationService()
    message_service = MessageService()
    return ChatService(conversation_service, message_service)

@router.post("/", response_model=schemas.ChatResponse)
async def chat_with_agent(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Chat with an agent
    
    This endpoint allows you to send a message to an agent and receive a response.
    If no conversation_id is provided, a new conversation will be created.
    
    Args:
        request: Chat request containing message, agent_id, and optional conversation_id
        db: Database session
        chat_service: Chat service instance
        
    Returns:
        ChatResponse with agent response and conversation details
    """
    try:
        # Validate agent exists
        agent = get_agent(db, request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
        
        # Process chat request
        result = await chat_service.chat_with_agent(
            db=db,
            agent_id=request.agent_id,
            user_message=request.message,
            conversation_id=request.conversation_id,
            context=request.context
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Return response
        return schemas.ChatResponse(
            success=True,
            message=result["message"],
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            agent_response=result["agent_response"],
            context=result["context"],
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}") 