from pydantic import BaseModel, Field
from datetime import datetime
from enum import StrEnum
from ._conversation import HandlerMessage


class TemplateGenerationStatus(StrEnum):
    """Status for template generation."""

    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class InterviewTemplateBase(BaseModel):
    name: str | None = None
    description: str | None = None
    version: str | None = None
    template_metadata: dict = Field(default_factory=dict)


class InterviewTemplateCreate(InterviewTemplateBase):
    kp_id: int
    source_template_id: int | None = None


class InterviewTemplateUpdate(InterviewTemplateBase):
    pass


class InterviewTemplateRead(InterviewTemplateBase):
    id: int
    kp_id: int
    folder_path: str
    is_active: bool
    is_master: bool
    created_at: datetime
    updated_at: datetime
    readme_content: str | None = None

    class Config:
        from_attributes = True


class InterviewSessionBase(BaseModel):
    session_name: str | None = None
    status: str = "draft"
    interviewee_name: str | None = None
    interviewee_role: str | None = None
    session_metadata: dict = Field(default_factory=dict)


class InterviewSessionCreate(InterviewSessionBase):
    interview_template_id: int
    conversation_id: int | None = None


class InterviewSessionUpdate(BaseModel):
    session_name: str | None = None
    status: str | None = None
    interviewee_name: str | None = None
    interviewee_role: str | None = None
    session_metadata: dict | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class InterviewSessionRead(InterviewSessionBase):
    id: int
    interview_template_id: int
    conversation_id: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Response schemas for API endpoints
class InterviewTemplateResponse(BaseModel):
    success: bool
    message: str
    data: InterviewTemplateRead | None = None
    error: str | None = None


class InterviewTemplateListResponse(BaseModel):
    success: bool
    message: str
    data: list[InterviewTemplateRead] = Field(default_factory=list)
    total: int = 0
    error: str | None = None


class InterviewSessionResponse(BaseModel):
    success: bool
    message: str
    data: InterviewSessionRead | None = None
    error: str | None = None


class InterviewSessionListResponse(BaseModel):
    success: bool
    message: str
    data: list[InterviewSessionRead] = Field(default_factory=list)
    total: int = 0
    error: str | None = None


class InterviewTemplateWithSessions(InterviewTemplateRead):
    """Interview template with nested sessions"""

    interview_sessions: list[InterviewSessionRead] = Field(default_factory=list)

    @property
    def session_count(self) -> int:
        return len(self.interview_sessions)

    @property
    def completed_sessions(self) -> list[InterviewSessionRead]:
        return [s for s in self.interview_sessions if s.status == "completed"]

    @property
    def active_sessions(self) -> list[InterviewSessionRead]:
        return [s for s in self.interview_sessions if s.status == "in_progress"]


class TemplateFinetuneChannelResponse(BaseModel):
    """Response for template fine-tune chat endpoint"""

    success: bool
    template_modified: bool
    agent_response: str
    internal_conversation: list[HandlerMessage] = Field(default_factory=list)
    error: str | None = None
