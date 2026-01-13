from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import StrEnum
from ._conversation import HandlerMessage
from ._interview_session import InterviewSessionRead


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
    folder_path: str | None = None  # Optional for duplication
    is_active: bool = True
    is_master: bool = False
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

    model_config = ConfigDict(from_attributes=True)


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


class TemplateDiffSection(BaseModel):
    """Represents a section of the template diff"""
    
    type: str  # 'add', 'remove', or 'unchanged'
    content: str
    line_start: int | None = None
    line_end: int | None = None


class TemplateDiff(BaseModel):
    """Represents the difference between old and new template content"""
    
    sections: list[TemplateDiffSection] = Field(default_factory=list)
    old_content: str | None = None
    new_content: str | None = None


class TemplateFinetuneChannelResponse(BaseModel):
    """Response for template fine-tune chat endpoint"""

    success: bool
    template_modified: bool
    agent_response: str
    internal_conversation: list[HandlerMessage] = Field(default_factory=list)
    template_diff: TemplateDiff | None = None
    error: str | None = None
