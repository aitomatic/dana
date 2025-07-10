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
