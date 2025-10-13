from __future__ import annotations
from pydantic import BaseModel, BeforeValidator, ConfigDict
from datetime import datetime
from typing import Annotated
from dana.lang.api.core.schemas import Specialization, MessageData
from ._conversation import HandlerMessage
from ._kp_structuring import DomainKnowledgeTreeV2
from ._common import BaseAPIResponse
from ._interview_template import InterviewTemplateWithSessions
from ._kp_generation import KnowledgeGenerationStatus


class KnowledgePackResponse(BaseModel):
    success: bool
    is_tree_modified: bool = False
    agent_response: str
    internal_conversation: list[HandlerMessage] = []
    error: str | None = None


class KnowledgePackOutput(BaseModel):
    id: int
    folder_path: Annotated[str, BeforeValidator(lambda v: str(v))]
    status: KnowledgeGenerationStatus = KnowledgeGenerationStatus.DRAFT
    kp_metadata: dict = {}
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(use_enum_values=True)

    # Interview templates with their sessions nested inside
    interview_templates: list[InterviewTemplateWithSessions] = []

    def get_specialization_info(self) -> Specialization:
        return Specialization(
            domain=self.kp_metadata.get("domain", "General"),
            role=self.kp_metadata.get("role", "Domain Expert"),
            task=self.kp_metadata.get("task", "Answer Questions"),
        )

    @property
    def active_templates(self) -> list[InterviewTemplateWithSessions]:
        """Get all active interview templates"""
        return [t for t in self.interview_templates if t.is_active]

    @property
    def master_template(self) -> InterviewTemplateWithSessions | None:
        """Get the master template for this knowledge pack"""
        return next((t for t in self.interview_templates if t.is_master), None)

    @property
    def template_count(self) -> int:
        """Get the total number of interview templates"""
        return len(self.interview_templates)

    @property
    def total_session_count(self) -> int:
        """Get the total number of interview sessions across all templates"""
        return sum(len(t.interview_sessions) for t in self.interview_templates)


class PaginationInfo(BaseModel):
    """Pagination metadata for list endpoints"""

    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool
    next_page: int | None
    previous_page: int | None


class PaginatedKnowledgePackResponse(BaseModel):
    """Paginated response for knowledge pack listings"""

    data: list[KnowledgePackOutput]
    pagination: PaginationInfo


class KnowledgePackCreateRequest(BaseModel):
    specialization: Specialization
    document_ids: list[int] = []  # Optional document IDs to associate


class KnowledgePackUpdateRequest(KnowledgePackCreateRequest):
    kp_id: int


class KnowledgePackSmartChatResponse(BaseAPIResponse):
    is_tree_modified: bool = False
    agent_response: str
    internal_conversation: list[MessageData] = []


# New schema for associating documents
class KnowledgePackAssociateDocumentsRequest(BaseModel):
    document_ids: list[int]


class KnowledgePackAssociateDocumentsResponse(BaseAPIResponse):
    associated_count: int = 0


class KnowledgePackDeleteResponse(BaseAPIResponse):
    pass


# Response schemas for endpoints that currently use HTTPException
class KnowledgePackGetResponse(BaseAPIResponse):
    data: DomainKnowledgeTreeV2 | dict | None = None


class KnowledgePackCreateResponse(BaseAPIResponse):
    data: KnowledgePackOutput | None = None


class KnowledgePackUpdateResponse(BaseAPIResponse):
    data: KnowledgePackOutput | None = None
