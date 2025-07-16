import shutil
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from dana.core.lang.dana_sandbox import DanaSandbox
from dana.core.lang.sandbox_context import SandboxContext

import logging
from . import models, schemas
from .models import Conversation, Message
from .schemas import ConversationCreate, MessageCreate, RunNAFileRequest, RunNAFileResponse

# Set up logging
logger = logging.getLogger(__name__)


def _copy_selected_documents_to_agent_folder(db: Session, agent_id: Any, document_ids: list[int]):
    """
    Copy selected documents to an agent-specific folder.
    
    Args:
        db: Database session
        agent_id: ID of the agent
        document_ids: List of document IDs to copy
    """
    if not document_ids:
        logger.info("No documents to copy")
        return
    
    # Create agent-specific folder
    agent_folder = Path(f"./uploads/agents/{agent_id}")
    agent_folder.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created agent folder: {agent_folder}")
    
    # Get documents from database
    documents = db.query(models.Document).filter(models.Document.id.in_(document_ids)).all()
    logger.info(f"Found {len(documents)} documents to copy")
    
    copied_count = 0
    for document in documents:
        try:
            # Get source file path
            source_path = Path(f"./uploads/{document.file_path}")
            if not source_path.exists():
                logger.warning(f"Source file not found: {source_path}")
                continue
            
            # Create destination path in agent folder
            dest_path = agent_folder / document.filename
            # Copy file to agent folder
            shutil.copy2(str(source_path), str(dest_path))
            
            # Update document record to point to agent folder
            document.file_path = f"agents/{agent_id}/{document.filename}"
            document.agent_id = int(agent_id)
            logger.info(f"Copied document {document.id} to agent folder: {dest_path}")
            copied_count += 1
            
        except Exception as e:
            logger.error(f"Error copying document {document.id}: {e}")
    
    # Commit changes to database
    db.commit()
    logger.info(f"Successfully copied {copied_count} documents to agent {agent_id} folder")


def get_agent(db: Session, agent_id: int):
    return db.query(models.Agent).filter(models.Agent.id == agent_id).first()


def get_agents(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Agent).order_by(models.Agent.id).offset(skip).limit(limit).all()


def create_agent(db: Session, agent: schemas.AgentCreate):
    db_agent = models.Agent(name=agent.name, description=agent.description, config=agent.config)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    # Handle selected knowledge (files and topics)
    if agent.config and 'selectedKnowledge' in agent.config:
        selected_knowledge = agent.config['selectedKnowledge']
        logger.info(f"Processing selected knowledge for agent {db_agent.id}: {selected_knowledge}")
        
        # Create agent-specific folder and copy selected files
        if selected_knowledge.get('documents'):
            print(f"Documents: {selected_knowledge['documents']}")
            agent_id = db_agent.id  # Get the actual integer value
            logger.info(f"Copying {len(selected_knowledge['documents'])} documents to agent folder")
            _copy_selected_documents_to_agent_folder(db, agent_id, selected_knowledge['documents'])
    
    return db_agent


class AgentService:
    def create_agent(self, db: Session, name: str, description: str, config: dict) -> models.Agent:
        agent = models.Agent(name=name, description=description, config=config)
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    def get_agents(self, db: Session, skip: int = 0, limit: int = 100) -> list[models.Agent]:
        return db.query(models.Agent).order_by(models.Agent.id).offset(skip).limit(limit).all()

    def get_agent(self, db: Session, agent_id: int) -> models.Agent | None:
        return db.query(models.Agent).filter(models.Agent.id == agent_id).first()

    def update_agent(self, db: Session, agent_id: int, name: str, description: str, config: dict) -> models.Agent | None:
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

    def get_topics(self, db: Session, skip: int = 0, limit: int = 100) -> list[models.Topic]:
        return db.query(models.Topic).offset(skip).limit(limit).all()

    def get_topic(self, db: Session, topic_id: int) -> models.Topic | None:
        return db.query(models.Topic).filter(models.Topic.id == topic_id).first()

    def update_topic(self, db: Session, topic_id: int, topic: schemas.TopicCreate) -> models.Topic | None:
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

    def get_documents(self, db: Session, skip: int = 0, limit: int = 100, topic_id: int | None = None) -> list[models.Document]:
        query = db.query(models.Document)
        if topic_id is not None:
            query = query.filter(models.Document.topic_id == topic_id)
        return query.offset(skip).limit(limit).all()

    def get_document(self, db: Session, document_id: int) -> models.Document | None:
        return db.query(models.Document).filter(models.Document.id == document_id).first()

    def update_document(self, db: Session, document_id: int, document_data: schemas.DocumentUpdate) -> models.Document | None:
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

    def get_file_path(self, document_id: int, db: Session) -> Path | None:
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
        db_convo = Conversation(
            title=conversation.title,
            agent_id=conversation.agent_id
        )
        db.add(db_convo)
        db.commit()
        db.refresh(db_convo)
        return db_convo

    def get_conversations(self, db: Session, skip: int = 0, limit: int = 100, agent_id: int | None = None) -> list[Conversation]:
        query = db.query(Conversation)
        if agent_id is not None:
            query = query.filter(Conversation.agent_id == agent_id)
        return query.order_by(Conversation.created_at.desc()).offset(skip).limit(limit).all()

    def get_conversation(self, db: Session, conversation_id: int) -> Conversation | None:
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def update_conversation(self, db: Session, conversation_id: int, conversation: ConversationCreate) -> Conversation | None:
        db_convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if db_convo:
            db_convo.title = conversation.title
            db_convo.agent_id = conversation.agent_id
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
        message = db.query(Message).filter(
            Message.id == message_id,
            Message.conversation_id == conversation_id
        ).first()
        if message:
            db.delete(message)
            db.commit()
            return True
        return False


class ChatService:
    """Service for handling chat interactions with agents"""
    
    def __init__(self, conversation_service: ConversationService, message_service: MessageService):
        self.conversation_service = conversation_service
        self.message_service = message_service
    
    async def chat_with_agent(
        self, 
        db: Session, 
        agent_id: int, 
        user_message: str, 
        conversation_id: int | None = None,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Chat with an agent and return the response
        """
        agent_msg = None
        try:
            # 1. If conversation_id is provided, check if it exists before agent execution
            if conversation_id is not None:
                conversation = self.conversation_service.get_conversation(db, conversation_id)
                if not conversation:
                    return {
                        "success": False,
                        "message": user_message,
                        "conversation_id": conversation_id,
                        "message_id": 0,
                        "agent_response": "",
                        "context": context,
                        "error": f"Conversation {conversation_id} not found"
                    }
            # 2. If conversation_id is None, create the conversation before agent execution
            else:
                conversation = self.conversation_service.create_conversation(
                    db, 
                    schemas.ConversationCreate(
                        title=f"Chat with Agent {agent_id}",
                        agent_id=agent_id
                    )
                )
                conversation_id = conversation.id
            if conversation_id is None:
                return {
                    "success": False,
                    "message": user_message,
                    "conversation_id": 0,
                    "message_id": 0,
                    "agent_response": "",
                    "context": context,
                    "error": "Failed to create or retrieve conversation"
                }
            # Create user message before agent execution
            user_msg = self.message_service.create_message(
                db,
                conversation_id,
                schemas.MessageCreate(sender="user", content=user_message)
            )
            try:
                agent_response = await self._execute_agent(db, agent_id, user_message, context)
            except Exception as e:
                return {
                    "success": False,
                    "message": user_message,
                    "conversation_id": conversation_id,
                    "message_id": user_msg.id,
                    "agent_response": "",
                    "context": context,
                    "error": str(e)
                }
            agent_msg = self.message_service.create_message(
                db,
                conversation_id,
                schemas.MessageCreate(sender="agent", content=agent_response)
            )
            return {
                "success": True,
                "message": user_message,
                "conversation_id": conversation_id,
                "message_id": agent_msg.id,
                "agent_response": agent_response,
                "context": context,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": user_message,
                "conversation_id": conversation_id or 0,
                "message_id": user_msg.id if 'user_msg' in locals() else 0,
                "agent_response": "",
                "context": context,
                "error": str(e)
            }
    
    async def _execute_agent(self, db: Session, agent_id: int, message: str, context: dict[str, Any] | None = None) -> str:
        """
        Execute agent with the given message and context
        
        Args:
            db: Database session
            agent_id: ID of the agent
            message: User message
            context: Optional context
            
        Returns:
            Agent response string
        """
        # Load agent from database
        agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Get Dana code from agent configuration
        dana_code = agent.config.get("dana_code", "")
        if not dana_code:
            raise ValueError(f"Agent {agent_id} has no Dana code configured")
        
        print(f"Executing agent {agent_id} ({agent.name}) with message: '{message}'")
        print(f"Using Dana code: {dana_code[:200]}...")
        
        # Parse agent name from Dana code
        agent_name_match = re.search(r'^\s*agent\s+([A-Za-z_][A-Za-z0-9_]*)\s*:', dana_code, re.MULTILINE)
        if not agent_name_match:
            raise ValueError("Could not find agent name in Dana code.")
        agent_name = agent_name_match.group(1)
        instance_var = agent_name[0].lower() + agent_name[1:]  # e.g., WeatherAgent -> weatherAgent
        # Append code to instantiate and solve using method call
        appended_code = f"\n{instance_var} = {agent_name}()\nresponse = {instance_var}.solve(\"{message.replace('\\', '\\\\').replace('"', '\\"')}\")\nprint(response)\n"
        dana_code_to_run = dana_code + appended_code
        
        # Create a temporary file for the Dana code
        temp_folder = Path("/tmp/dana_code")
        temp_folder.mkdir(parents=True, exist_ok=True)
        full_path = temp_folder / f"agent_{agent_id}_code.na"

        print(f"Dana code to run: {dana_code_to_run}")
        
        # Write the Dana code to the temporary file
        with open(full_path, "w") as f:
            f.write(dana_code_to_run)
        
        # Execute the Dana code using DanaSandbox
        sandbox_context = SandboxContext()
        
        # If the agent has selected knowledge (documents), add them to the context
        selected_knowledge = agent.config.get("selectedKnowledge", {})
        if selected_knowledge and "documents" in selected_knowledge:
            # Add document paths to the context if needed
            print(f"Agent has {len(selected_knowledge['documents'])} selected documents")
        
        try:
            DanaSandbox.quick_run(file_path=full_path, context=sandbox_context)
        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            print(error_msg)
            raise RuntimeError(error_msg)

        print("--------------------------------")
        print(sandbox_context.get_state())

        state = sandbox_context.get_state()
        response_text = state.get("local", { }).get("response", "")

        return response_text
