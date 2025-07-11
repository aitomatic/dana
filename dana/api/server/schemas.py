from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AgentBase(BaseModel):
    name: str
    description: str
    config: dict[str, Any]


class AgentCreate(AgentBase):
    pass


class AgentRead(AgentBase):
    id: int

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


class AgentGenerationResponse(BaseModel):
    """Response schema for agent generation endpoint"""
    success: bool
    dana_code: str
    agent_name: str | None = None
    agent_description: str | None = None
    error: str | None = None


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
    code: str
    agent_name: str | None = None
    description: str | None = None


class CodeValidationResponse(BaseModel):
    """Response schema for code validation endpoint"""
    success: bool
    is_valid: bool
    errors: list[CodeError] = []
    warnings: list[CodeWarning] = []
    suggestions: list[CodeSuggestion] = []
    fixed_code: str | None = None
    error: str | None = None


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
