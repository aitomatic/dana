from dana.studio.api.core.schemas_v2._common import BaseAPIResponse
from dana.studio.api.core.schemas import MessageData
from pydantic import BaseModel
from enum import StrEnum


class KnowledgeGenerationStatus(StrEnum):
    """Status for knowledge generation."""

    DRAFT = "draft"
    PENDING = "pending"
    GENERATING = "generating"
    QUESTION_GENERATED = "question_generated"
    COMPLETED = "completed"
    FAILED = "failed"


class KnowledgeGenerationResponse(BaseAPIResponse):
    """Response for starting knowledge generation."""

    task_id: int | None = None


class TemplateFinetuneRequest(BaseModel):
    """Request for template fine-tuning session"""

    user_message: str
    chat_history: list[MessageData] = []
    knowledge_id: int


class TemplateFinetuneResponse(BaseAPIResponse):
    """Response from template fine-tuning handler"""

    status: str  # "success", "user_input_required"
    message: str
    conversation: list[MessageData]
    template_modified: bool = False
    template_preview: str | None = None
