from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AgentBase(BaseModel):
    name: str
    description: str
    config: dict[str, Any]


class AgentCreate(AgentBase):
    pass


class AgentDeployRequest(BaseModel):
    """Request schema for agent deployment endpoint"""

    name: str
    description: str
    config: dict[str, Any]
    dana_code: str | None = None  # For single file deployment
    multi_file_project: MultiFileProject | None = None  # For multi-file deployment

    def __init__(self, **data):
        # Ensure at least one deployment method is provided
        super().__init__(**data)
        if not self.dana_code and not self.multi_file_project:
            raise ValueError("Either 'dana_code' or 'multi_file_project' must be provided")
        if self.dana_code and self.multi_file_project:
            raise ValueError("Cannot provide both 'dana_code' and 'multi_file_project'")


class AgentDeployResponse(BaseModel):
    """Response schema for agent deployment endpoint"""

    success: bool
    agent: AgentRead | None = None
    error: str | None = None


class AgentRead(AgentBase):
    id: int
    folder_path: str | None = None
    files: list[str] | None = None

    # Two-phase generation fields
    generation_phase: str = "description"
    agent_description_draft: dict | None = None
    generation_metadata: dict | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TopicBase(BaseModel):
    name: str
    description: str


class TopicCreate(TopicBase):
    pass


class TopicRead(TopicBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentBase(BaseModel):
    original_filename: str
    topic_id: int | None = None
    agent_id: int | None = None


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    id: int
    filename: str
    file_size: int
    mime_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUpdate(BaseModel):
    original_filename: str | None = None
    topic_id: int | None = None
    agent_id: int | None = None


class RunNAFileRequest(BaseModel):
    file_path: str
    input: Any = None


class RunNAFileResponse(BaseModel):
    success: bool
    output: str | None = None
    result: Any = None
    error: str | None = None
    final_context: dict[str, Any] | None = None


class ConversationBase(BaseModel):
    title: str
    agent_id: int


class ConversationCreate(ConversationBase):
    pass


class ConversationRead(ConversationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageBase(BaseModel):
    sender: str
    content: str


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessages(ConversationRead):
    messages: list[MessageRead] = []


# Chat-specific schemas
class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""

    message: str
    conversation_id: int | None = None
    agent_id: int
    context: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""

    success: bool
    message: str
    conversation_id: int
    message_id: int
    agent_response: str
    context: dict[str, Any] | None = None
    error: str | None = None


# Georgia Training schemas
class MessageData(BaseModel):
    """Schema for a single message in conversation"""

    role: str  # 'user' or 'assistant'
    content: str


class AgentGenerationRequest(BaseModel):
    """Request schema for Georgia training endpoint"""

    messages: list[MessageData]
    current_code: str | None = None
    multi_file: bool = False  # New field to enable multi-file training

    # Two-phase training fields
    phase: str = "description"  # 'description' | 'code_generation'
    agent_id: int | None = None  # For Phase 2 requests

    # Agent data from client (for Phase 2 when agent not yet in DB)
    agent_data: dict | None = None


class AgentCapabilities(BaseModel):
    """Agent capabilities extracted from analysis"""

    summary: str | None = None
    knowledge: list[str] | None = None
    workflow: list[str] | None = None
    tools: list[str] | None = None


class DanaFile(BaseModel):
    """Schema for a single Dana file"""

    filename: str
    content: str
    file_type: str  # 'agent', 'workflow', 'resources', 'methods', 'common'
    description: str | None = None
    dependencies: list[str] = []  # Files this file depends on


class MultiFileProject(BaseModel):
    """Schema for a multi-file Dana project"""

    name: str
    description: str
    files: list[DanaFile]
    main_file: str  # Primary entry point file
    structure_type: str  # 'simple', 'modular', 'complex'


class AgentGenerationResponse(BaseModel):
    """Response schema for agent generation endpoint"""

    success: bool
    dana_code: str | None = None  # Optional in Phase 1
    error: str | None = None

    # Essential agent info
    agent_name: str | None = None
    agent_description: str | None = None

    # Agent capabilities analysis
    capabilities: AgentCapabilities | None = None

    # File paths for opening in explorer
    auto_stored_files: list[str] | None = None

    # Multi-file support (minimal)
    multi_file_project: MultiFileProject | None = None

    # Conversation guidance (only when needed)
    needs_more_info: bool = False
    follow_up_message: str | None = None
    suggested_questions: list[str] | None = None

    # New fields for agent folder and id
    agent_id: int | None = None
    agent_folder: str | None = None

    # Two-phase generation fields
    phase: str = "description"  # Current phase of generation
    ready_for_code_generation: bool = False  # Whether description is sufficient for Phase 2

    # Temporary agent data for Phase 1 (not stored in DB yet)
    temp_agent_data: dict | None = None


# Phase 1 specific schemas
class AgentDescriptionRequest(BaseModel):
    """Request schema for Phase 1 agent description refinement"""

    messages: list[MessageData]
    agent_id: int | None = None  # For updating existing draft
    agent_data: dict | None = None  # Current agent object for modification


class AgentDescriptionResponse(BaseModel):
    """Response schema for Phase 1 agent description refinement"""

    success: bool
    agent_id: int
    agent_name: str | None = None
    agent_description: str | None = None
    capabilities: AgentCapabilities | None = None
    follow_up_message: str | None = None
    suggested_questions: list[str] | None = None
    ready_for_code_generation: bool | None = None
    agent_folder: str | None = None
    error: str | None = None


class AgentCodeGenerationRequest(BaseModel):
    """Request schema for Phase 2 code generation"""

    agent_id: int
    multi_file: bool = False


class DanaSyntaxCheckRequest(BaseModel):
    """Request schema for Dana code syntax check endpoint"""

    dana_code: str


class DanaSyntaxCheckResponse(BaseModel):
    """Response schema for Dana code syntax check endpoint"""

    success: bool
    error: str | None = None
    output: str | None = None


# Code Validation schemas
class CodeError(BaseModel):
    """Schema for a code error"""

    line: int
    column: int
    message: str
    severity: str  # 'error' or 'warning'
    code: str


class CodeWarning(BaseModel):
    """Schema for a code warning"""

    line: int
    column: int
    message: str
    suggestion: str


class CodeSuggestion(BaseModel):
    """Schema for a code suggestion"""

    type: str  # 'syntax', 'best_practice', 'performance', 'security'
    message: str
    code: str
    description: str


class CodeValidationRequest(BaseModel):
    """Request schema for code validation endpoint"""

    code: str | None = None  # For single-file validation (backward compatibility)
    agent_name: str | None = None
    description: str | None = None

    # New multi-file support
    multi_file_project: MultiFileProject | None = None  # For multi-file validation

    def __init__(self, **data):
        # Ensure at least one validation method is provided
        super().__init__(**data)
        if not self.code and not self.multi_file_project:
            raise ValueError("Either 'code' or 'multi_file_project' must be provided")
        if self.code and self.multi_file_project:
            raise ValueError("Cannot provide both 'code' and 'multi_file_project'")


class CodeValidationResponse(BaseModel):
    """Response schema for code validation endpoint"""

    success: bool
    is_valid: bool
    errors: list[CodeError] = []
    warnings: list[CodeWarning] = []
    suggestions: list[CodeSuggestion] = []
    fixed_code: str | None = None
    error: str | None = None

    # Multi-file validation results
    file_results: list[dict] | None = None  # Results for each file in multi-file project
    dependency_errors: list[dict] | None = None  # Dependency validation errors
    overall_errors: list[dict] | None = None  # Project-level errors


class CodeFixRequest(BaseModel):
    """Request schema for code auto-fix endpoint"""

    code: str
    errors: list[CodeError]
    agent_name: str | None = None
    description: str | None = None


class CodeFixResponse(BaseModel):
    """Response schema for code auto-fix endpoint"""

    success: bool
    fixed_code: str
    applied_fixes: list[str] = []
    remaining_errors: list[CodeError] = []
    error: str | None = None


class ProcessAgentDocumentsRequest(BaseModel):
    """Request schema for processing agent documents"""

    document_folder: str
    conversation: str | list[str]
    summary: str
    agent_data: dict | None = None  # Include current agent data (name, description, capabilities, etc.)
    current_code: str | None = None  # Current dana code to be updated
    multi_file_project: dict | None = None  # Current multi-file project structure


class ProcessAgentDocumentsResponse(BaseModel):
    """Response schema for processing agent documents"""

    success: bool
    message: str
    agent_name: str | None = None
    agent_description: str | None = None
    processing_details: dict | None = None
    # Include updated code with RAG integration
    dana_code: str | None = None  # Updated single-file code
    multi_file_project: dict | None = None  # Updated multi-file project with RAG integration
    error: str | None = None


class KnowledgeUploadRequest(BaseModel):
    """Request schema for knowledge file upload with conversation context"""

    agent_id: str | None = None
    agent_folder: str | None = None
    conversation_context: list[MessageData] | None = None  # Current conversation
    agent_info: dict | None = None  # Current agent info for regeneration
