from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship

from .database import Base
from .schemas_v2 import KnowledgeGenerationStatus


class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    config = Column(JSON)
    folder_path = Column(String, nullable=True)  # Path to agent folder
    files = Column(JSON, nullable=True)  # List of .na file paths

    # Two-phase generation fields
    generation_phase = Column(String, default="description", nullable=False)  # 'description', 'code_generated'
    agent_description_draft = Column(JSON, nullable=True)  # Structured description data during Phase 1
    generation_metadata = Column(JSON, nullable=True)  # Conversation context and requirements

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    documents = relationship("Document", back_populates="agent")
    kp_agent_rs = relationship("KnowledgeAgentRelationship", back_populates="agent")


class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    documents = relationship("Document", back_populates="topic")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    filename = Column(String, index=True)  # UUID filename
    original_filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    agent_id = Column(
        Integer, ForeignKey("agents.id"), nullable=True
    )  # TODO : For now a single document can only be associated with a single agent, workaround by using `agent.config["associated_documents"]` to manage association
    # For JSON extraction files: link to the original PDF document
    source_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    doc_metadata = Column("metadata", JSON, nullable=True, default={})

    topic = relationship("Topic", back_populates="documents")
    agent = relationship("Agent", back_populates="documents")
    # Self-referential relationship for extraction files
    source_document = relationship("Document", remote_side=[id], foreign_keys=[source_document_id], back_populates="extraction_files")
    extraction_files = relationship("Document", foreign_keys=[source_document_id], back_populates="source_document")


class Conversation(Base):
    __tablename__ = "conversations_v2"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String, nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)
    kp_id = Column(Integer, ForeignKey("knowledge_packs.id"), nullable=True, index=True)
    template_id = Column(Integer, ForeignKey("interview_templates.id"), nullable=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=True, index=True)
    code_gen_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)  # Conversation for code generation
    type = Column(String, nullable=True, default="chat_with_agent")  # NOTE: Assume that number of types is small, so we won't index it
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    agent = relationship("Agent", foreign_keys=[agent_id])
    code_gen_agent = relationship("Agent", foreign_keys=[code_gen_id])
    knowledge_pack = relationship("KnowledgePack", foreign_keys=[kp_id])
    template = relationship("InterviewTemplate", foreign_keys=[template_id], back_populates="conversation", uselist=False)  # ONE-TO-ONE
    session = relationship("InterviewSession", foreign_keys=[session_id], back_populates="conversation", uselist=False)  # ONE-TO-ONE


class Message(Base):
    __tablename__ = "messages_v2"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations_v2.id"), nullable=False, index=True)
    sender = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    require_user = Column(Boolean, nullable=False, default=False)
    treat_as_tool = Column(Boolean, nullable=False, default=False)
    msg_metadata = Column("metadata", JSON, nullable=False, default={})
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    conversation = relationship("Conversation", back_populates="messages")


# class ConversationDeprecated(Base):
#     __tablename__ = "conversations"
#     id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     title = Column(String, nullable=False)
#     agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
#     created_at = Column(DateTime, default=lambda: datetime.now(UTC))
#     updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
#     messages = relationship("MessageDeprecated", back_populates="conversation", cascade="all, delete-orphan")
#     agent = relationship("Agent")


# class MessageDeprecated(Base):
#     __tablename__ = "messages"
#     id = Column(Integer, primary_key=True, autoincrement=True, index=True)
#     conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
#     sender = Column(String, nullable=False)
#     content = Column(Text, nullable=False)
#     created_at = Column(DateTime, default=lambda: datetime.now(UTC))
#     updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
#     conversation = relationship("ConversationDeprecated", back_populates="messages")


class AgentChatHistory(Base):
    __tablename__ = "agent_chat_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    sender = Column(String, nullable=False)  # 'user' or 'agent'
    text = Column(Text, nullable=False)
    type = Column(String, nullable=False, default="chat_with_dana_build")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class KnowledgePack(Base):
    __tablename__ = "knowledge_packs"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    kp_metadata = Column("metadata", JSON, default={})
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    kp_agent_rs = relationship("KnowledgeAgentRelationship", back_populates="knowledge_pack")
    source_kp_id = Column(Integer, ForeignKey("knowledge_packs.id"), nullable=True, index=True)
    source_kp = relationship("KnowledgePack", remote_side=[id], foreign_keys=[source_kp_id], back_populates="child_kps")
    child_kps = relationship("KnowledgePack", foreign_keys=[source_kp_id], back_populates="source_kp")
    status = Column(String, nullable=True, default=KnowledgeGenerationStatus.DRAFT)
    generation_task_id = Column(Integer, ForeignKey("background_tasks.id"), nullable=True)
    generation_task = relationship("BackGroundTask", foreign_keys=[generation_task_id])

    # NEW RELATIONSHIP
    interview_templates = relationship("InterviewTemplate", back_populates="knowledge_pack", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="knowledge_pack", cascade="all, delete-orphan")


class InterviewTemplate(Base):
    __tablename__ = "interview_templates"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    kp_id = Column(Integer, ForeignKey("knowledge_packs.id"), nullable=False, index=True)

    # Template identification
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(String, nullable=False, default="1.0.0")

    # Template file and metadata
    folder_path = Column(String, nullable=False)  # Relative path to current working directory
    is_active = Column(Boolean, nullable=False, default=True)  # Active template for the KP
    is_master = Column(Boolean, nullable=False, default=False)  # Master template (generated from KP)

    # Template metadata
    template_metadata = Column("metadata", JSON, nullable=True, default={})
    # Possible metadata fields:
    # - domain: str
    # - role: str
    # - estimated_duration: int (minutes)
    # - total_topics: int
    # - last_modified_by: str
    # - modification_history: list

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    knowledge_pack = relationship("KnowledgePack", back_populates="interview_templates")
    interview_sessions = relationship("InterviewSession", back_populates="interview_template", cascade="all, delete-orphan")
    conversation = relationship("Conversation", back_populates="template", cascade="all, delete-orphan", uselist=False)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    interview_template_id = Column(Integer, ForeignKey("interview_templates.id"), nullable=False, index=True)

    # Session identification
    session_name = Column(String, nullable=True)  # Optional custom name

    # Session status
    status = Column(String, nullable=False, default="draft")
    # Status values: draft, in_progress, completed, cancelled

    # Interview participant info
    interviewee_name = Column(String, nullable=True)
    interviewee_role = Column(String, nullable=True)

    # Session metadata
    session_metadata = Column("metadata", JSON, nullable=True, default={})
    # Possible metadata fields:
    # - duration_minutes: int
    # - topics_covered: list[str]
    # - completion_percentage: float
    # - interviewer_notes: str
    # - recording_url: str
    # - transcript_path: str

    # Session folder path
    folder_path = Column(String, nullable=True)  # Path to session directory

    # Session results
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    interview_template = relationship("InterviewTemplate", back_populates="interview_sessions")
    conversation = relationship("Conversation", back_populates="session", cascade="all, delete-orphan", uselist=False)


class KnowledgeAgentRelationship(Base):
    __tablename__ = "knowledge_agent_relationships"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    knowledge_pack_id = Column(Integer, ForeignKey("knowledge_packs.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    knowledge_pack = relationship("KnowledgePack", back_populates="kp_agent_rs")
    agent = relationship("Agent", back_populates="kp_agent_rs")


class BackGroundTask(Base):
    __tablename__ = "background_tasks"
    # ONLY SUPPORT A SET OF PREDEFINED TASKS
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    data = Column(JSON, nullable=False, default={})
    task_hash = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class ApplicationSettings(Base):
    __tablename__ = "application_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String, nullable=False, index=True)  # e.g., "template_generation", "interview_system"
    key = Column(String, nullable=False, index=True)  # e.g., "prompt", "default_prompt", "system_prompt"
    full_key = Column(String, unique=True, nullable=False, index=True)  # category.key for unique constraint

    # Content
    value = Column(Text, nullable=True)  # The actual prompt content

    # Metadata for UI and documentation
    name = Column(String, nullable=True)  # Human-readable name: "Template Generation Prompt"
    description = Column(Text, nullable=True)  # What this prompt does
    placeholders = Column(JSON, nullable=True)  # Available placeholders: ["{formatted_summaries}", "{domain}", "{role}"]
    placeholder_examples = Column(JSON, nullable=True)  # Example values: {"{domain}": "Sugar Manufacturing", "{role}": "Process Engineer"}
    default_value = Column(Text, nullable=True)  # Hardcoded fallback for reference

    # Versioning and tracking
    version = Column(String, nullable=True, default="1.0.0")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Usage context
    applies_to = Column(String, nullable=True)  # e.g., "knowledge_pack", "interview_template", "global"
    is_active = Column(Boolean, default=True)
