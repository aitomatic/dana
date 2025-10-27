from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from ._conversation import HandlerMessage


class InterviewSessionBase(BaseModel):
    session_name: str | None = None
    status: str = "draft"
    interviewee_name: str | None = None
    interviewee_role: str | None = None
    session_metadata: dict = Field(default_factory=dict)
    folder_path: str | None = None


class InterviewSessionCreate(InterviewSessionBase):
    interview_template_id: int


class InterviewSessionUpdate(BaseModel):
    session_name: str | None = None
    status: str | None = None
    interviewee_name: str | None = None
    interviewee_role: str | None = None
    session_metadata: dict | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    folder_path: str | None = None


class InterviewSessionRead(InterviewSessionBase):
    id: int
    interview_template_id: int
    conversation_id: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    content: str | None = None  # Interview note content

    model_config = ConfigDict(from_attributes=True)


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


class InterviewChatResponse(BaseModel):
    """Response for interview session chat endpoint - matches TemplateFinetuneChannelResponse pattern"""

    success: bool
    interview_modified: bool  # Equivalent to template_modified
    agent_response: str
    internal_conversation: list[HandlerMessage] = Field(default_factory=list)
    error: str | None = None


class QuestionProgress(BaseModel):
    """Progress information for a single question"""

    question_text: str
    status: str  # "not_asked", "being_asked", "answered", "skipped"
    asked_at: datetime | None = None


class TopicProgress(BaseModel):
    """Progress information for a single interview topic"""

    topic_name: str
    status: str  # "not_started", "in_progress", "completed"
    completeness: int  # Percentage 0-100
    insights_count: int
    questions: list[QuestionProgress] = Field(default_factory=list)


class InterviewProgressData(BaseModel):
    """Aggregated progress data for entire interview session"""

    topics: list[TopicProgress] = Field(default_factory=list)
    overall_completeness: int  # Percentage 0-100
    current_topic: str | None = None


class InterviewProgressResponse(BaseModel):
    """Response for interview progress endpoint"""

    success: bool
    data: InterviewProgressData | None = None
    error: str | None = None
