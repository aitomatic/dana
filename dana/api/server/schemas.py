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


# Agent Generation schemas
class MessageData(BaseModel):
    """Schema for a single message in conversation"""
    role: str  # 'user' or 'assistant'
    content: str


class AgentGenerationRequest(BaseModel):
    """Request schema for agent generation endpoint"""
    messages: list[MessageData]
    current_code: str | None = None
    multi_file: bool = False  # New field to enable multi-file generation


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
    dana_code: str
    error: str | None = None
    
    # Essential agent info
    agent_name: str | None = None
    agent_description: str | None = None
    
    # File paths for opening in explorer
    auto_stored_files: list[str] | None = None
    
    # Multi-file support (minimal)
    multi_file_project: MultiFileProject | None = None
    
    # Conversation guidance (only when needed)
    needs_more_info: bool = False
    follow_up_message: str | None = None
    suggested_questions: list[str] | None = None


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
