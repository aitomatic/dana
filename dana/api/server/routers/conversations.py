from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import db, schemas
from ..services import ConversationService, MessageService

router = APIRouter(prefix="/conversations", tags=["conversations"])

def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

def get_conversation_service():
    return ConversationService()

def get_message_service():
    return MessageService()

# Conversation endpoints
@router.get("/", response_model=list[schemas.ConversationRead])
async def list_conversations(
    skip: int = 0, 
    limit: int = 100, 
    agent_id: int | None = None,
    db: Session = Depends(get_db), 
    service: ConversationService = Depends(get_conversation_service)
):
    return service.get_conversations(db, skip=skip, limit=limit, agent_id=agent_id)

@router.get("/{conversation_id}", response_model=schemas.ConversationWithMessages)
async def get_conversation(conversation_id: int, db: Session = Depends(get_db), service: ConversationService = Depends(get_conversation_service)):
    convo = service.get_conversation(db, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    # Eagerly load messages
    return schemas.ConversationWithMessages.model_validate({**convo.__dict__, "messages": convo.messages})

@router.post("/", response_model=schemas.ConversationRead)
async def create_conversation(conversation: schemas.ConversationCreate, db: Session = Depends(get_db), service: ConversationService = Depends(get_conversation_service)):
    return service.create_conversation(db, conversation)

@router.put("/{conversation_id}", response_model=schemas.ConversationRead)
async def update_conversation(conversation_id: int, conversation: schemas.ConversationCreate, db: Session = Depends(get_db), service: ConversationService = Depends(get_conversation_service)):
    updated = service.update_conversation(db, conversation_id, conversation)
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return updated

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int, db: Session = Depends(get_db), service: ConversationService = Depends(get_conversation_service)):
    success = service.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted successfully"}

# Message endpoints
@router.get("/{conversation_id}/messages/", response_model=list[schemas.MessageRead])
async def list_messages(conversation_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), service: MessageService = Depends(get_message_service)):
    return service.get_messages(db, conversation_id, skip=skip, limit=limit)

@router.get("/{conversation_id}/messages/{message_id}", response_model=schemas.MessageRead)
async def get_message(conversation_id: int, message_id: int, db: Session = Depends(get_db), service: MessageService = Depends(get_message_service)):
    msg = service.get_message(db, conversation_id, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg

@router.post("/{conversation_id}/messages/", response_model=schemas.MessageRead)
async def create_message(conversation_id: int, message: schemas.MessageCreate, db: Session = Depends(get_db), service: MessageService = Depends(get_message_service)):
    return service.create_message(db, conversation_id, message)

@router.put("/{conversation_id}/messages/{message_id}", response_model=schemas.MessageRead)
async def update_message(conversation_id: int, message_id: int, message: schemas.MessageCreate, db: Session = Depends(get_db), service: MessageService = Depends(get_message_service)):
    updated = service.update_message(db, conversation_id, message_id, message)
    if not updated:
        raise HTTPException(status_code=404, detail="Message not found")
    return updated

@router.delete("/{conversation_id}/messages/{message_id}")
async def delete_message(conversation_id: int, message_id: int, db: Session = Depends(get_db), service: MessageService = Depends(get_message_service)):
    success = service.delete_message(db, conversation_id, message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message deleted successfully"} 