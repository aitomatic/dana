from sqlalchemy.orm import Session
from . import models, schemas
import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile, HTTPException
# from dana.sandbox.dana_sandbox import DanaSandbox
from .schemas import RunNAFileRequest, RunNAFileResponse
from .models import Conversation, Message
from .schemas import ConversationCreate, ConversationRead, MessageCreate, MessageRead


def get_agent(db: Session, agent_id: int):
    return db.query(models.Agent).filter(models.Agent.id == agent_id).first()


def get_agents(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Agent).offset(skip).limit(limit).all()


def create_agent(db: Session, agent: schemas.AgentCreate):
    db_agent = models.Agent(name=agent.name, description=agent.description, config=agent.config)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


class AgentService:
    def create_agent(self, db: Session, name: str, description: str, config: dict) -> models.Agent:
        agent = models.Agent(name=name, description=description, config=config)
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    def get_agents(self, db: Session, skip: int = 0, limit: int = 100) -> List[models.Agent]:
        return db.query(models.Agent).offset(skip).limit(limit).all()

    def get_agent(self, db: Session, agent_id: int) -> Optional[models.Agent]:
        return db.query(models.Agent).filter(models.Agent.id == agent_id).first()

    def update_agent(self, db: Session, agent_id: int, name: str, description: str, config: dict) -> Optional[models.Agent]:
        agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
        if agent:
            agent.name = name
            agent.description = description
            agent.config = config
            db.commit()
            db.refresh(agent)
        return agent

    def delete_agent(self, db: Session, agent_id: int) -> bool:
        agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
        if agent:
            db.delete(agent)
            db.commit()
            return True
        return False


class FileStorageService:
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {".pdf", ".txt", ".md", ".json", ".csv", ".docx"}

    def validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        if file.size and file.size > self.max_file_size:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB")

        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}")

    def save_file(self, file: UploadFile) -> tuple[str, str, int]:
        """Save file and return (filename, file_path, file_size)"""
        # Generate unique filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Create date-based directory structure
        today = datetime.now()
        date_dir = self.upload_dir / str(today.year) / f"{today.month:02d}" / f"{today.day:02d}"
        date_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = date_dir / unique_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Get file size
        file_size = file_path.stat().st_size

        # Return relative path for database storage
        relative_path = str(file_path.relative_to(self.upload_dir))

        return unique_filename, relative_path, file_size

    def get_file_path(self, relative_path: str) -> Path:
        """Get absolute file path from relative path"""
        return self.upload_dir / relative_path

    def delete_file(self, relative_path: str) -> bool:
        """Delete file from storage"""
        try:
            file_path = self.get_file_path(relative_path)
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception:
            pass
        return False


class TopicService:
    def create_topic(self, db: Session, topic: schemas.TopicCreate) -> models.Topic:
        db_topic = models.Topic(name=topic.name, description=topic.description)
        db.add(db_topic)
        db.commit()
        db.refresh(db_topic)
        return db_topic

    def get_topics(self, db: Session, skip: int = 0, limit: int = 100) -> List[models.Topic]:
        return db.query(models.Topic).offset(skip).limit(limit).all()

    def get_topic(self, db: Session, topic_id: int) -> Optional[models.Topic]:
        return db.query(models.Topic).filter(models.Topic.id == topic_id).first()

    def update_topic(self, db: Session, topic_id: int, topic: schemas.TopicCreate) -> Optional[models.Topic]:
        db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
        if db_topic:
            db_topic.name = topic.name
            db_topic.description = topic.description
            db_topic.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_topic)
        return db_topic

    def delete_topic(self, db: Session, topic_id: int) -> bool:
        db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
        if db_topic:
            db.delete(db_topic)
            db.commit()
            return True
        return False


class DocumentService:
    def __init__(self, file_storage: FileStorageService):
        self.file_storage = file_storage

    def create_document(self, db: Session, file: UploadFile, document_data: schemas.DocumentCreate) -> models.Document:
        # Validate and save file
        self.file_storage.validate_file(file)
        filename, file_path, file_size = self.file_storage.save_file(file)

        # Create document record
        db_document = models.Document(
            filename=filename,
            original_filename=document_data.original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            topic_id=document_data.topic_id,
            agent_id=document_data.agent_id,
        )

        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document

    def get_documents(self, db: Session, skip: int = 0, limit: int = 100, topic_id: Optional[int] = None) -> List[models.Document]:
        query = db.query(models.Document)
        if topic_id is not None:
            query = query.filter(models.Document.topic_id == topic_id)
        return query.offset(skip).limit(limit).all()

    def get_document(self, db: Session, document_id: int) -> Optional[models.Document]:
        return db.query(models.Document).filter(models.Document.id == document_id).first()

    def update_document(self, db: Session, document_id: int, document_data: schemas.DocumentUpdate) -> Optional[models.Document]:
        db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
        if db_document:
            if document_data.original_filename is not None:
                db_document.original_filename = document_data.original_filename
            if document_data.topic_id is not None:
                db_document.topic_id = document_data.topic_id
            if document_data.agent_id is not None:
                db_document.agent_id = document_data.agent_id

            db_document.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_document)
        return db_document

    def delete_document(self, db: Session, document_id: int) -> bool:
        db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
        if db_document:
            # Delete file from storage
            self.file_storage.delete_file(str(db_document.file_path))

            # Delete database record
            db.delete(db_document)
            db.commit()
            return True
        return False

    def get_file_path(self, document_id: int, db: Session) -> Optional[Path]:
        """Get file path for download"""
        document = self.get_document(db, document_id)
        if document:
            return self.file_storage.get_file_path(str(document.file_path))
        return None


def run_na_file_service(request: RunNAFileRequest):
    """Run a DANA .na file using DanaSandbox and return the result."""
    try:
        print(f"Running .na file: {request.file_path}")

        # sandbox = DanaSandbox()
        # # Optionally set input in context if provided
        # if request.input is not None:
        #     sandbox._context.set("input", request.input)
        # result = sandbox.run(request.file_path)
        # # Convert final_context to dict[str, Any] if possible
        # final_ctx = None
        # if hasattr(result, "final_context") and result.final_context is not None:
        #     fc = result.final_context
        #     if hasattr(fc, "to_dict"):
        #         final_ctx = fc.to_dict()
        #     elif isinstance(fc, dict):
        #         final_ctx = fc
        #     else:
        #         final_ctx = None
        # return RunNAFileResponse(
        #     success=result.success,
        #     output=getattr(result, "output", None),
        #     result=getattr(result, "result", None),
        #     error=str(result.error) if result.error else None,
        #     final_context=final_ctx,
        # )
    except Exception as e:
        return RunNAFileResponse(success=False, error=str(e))


class ConversationService:
    def create_conversation(self, db: Session, conversation: ConversationCreate) -> Conversation:
        db_convo = Conversation(title=conversation.title)
        db.add(db_convo)
        db.commit()
        db.refresh(db_convo)
        return db_convo

    def get_conversations(self, db: Session, skip: int = 0, limit: int = 100) -> list[Conversation]:
        return db.query(Conversation).offset(skip).limit(limit).all()

    def get_conversation(self, db: Session, conversation_id: int) -> Conversation | None:
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def update_conversation(self, db: Session, conversation_id: int, conversation: ConversationCreate) -> Conversation | None:
        db_convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if db_convo:
            db_convo.title = conversation.title
            db_convo.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_convo)
        return db_convo

    def delete_conversation(self, db: Session, conversation_id: int) -> bool:
        db_convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if db_convo:
            db.delete(db_convo)
            db.commit()
            return True
        return False


class MessageService:
    def create_message(self, db: Session, conversation_id: int, message: MessageCreate) -> Message:
        db_msg = Message(conversation_id=conversation_id, sender=message.sender, content=message.content)
        db.add(db_msg)
        db.commit()
        db.refresh(db_msg)
        return db_msg

    def get_messages(self, db: Session, conversation_id: int, skip: int = 0, limit: int = 100) -> list[Message]:
        return db.query(Message).filter(Message.conversation_id == conversation_id).offset(skip).limit(limit).all()

    def get_message(self, db: Session, conversation_id: int, message_id: int) -> Message | None:
        return db.query(Message).filter(Message.conversation_id == conversation_id, Message.id == message_id).first()

    def update_message(self, db: Session, conversation_id: int, message_id: int, message: MessageCreate) -> Message | None:
        db_msg = db.query(Message).filter(Message.conversation_id == conversation_id, Message.id == message_id).first()
        if db_msg:
            db_msg.sender = message.sender
            db_msg.content = message.content
            db_msg.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_msg)
        return db_msg

    def delete_message(self, db: Session, conversation_id: int, message_id: int) -> bool:
        db_msg = db.query(Message).filter(Message.conversation_id == conversation_id, Message.id == message_id).first()
        if db_msg:
            db.delete(db_msg)
            db.commit()
            return True
        return False
