"""
Schema definitions for interview analysis API endpoints.
"""

from pydantic import BaseModel, BeforeValidator
from typing import Any, Annotated

DEFAULT_ANALYSIS_REPORT = "No insights captured yet"


class SessionInsight(BaseModel):
    session: str
    expert_insight: str
    status: str
    insights_count: int


class TopicAnalysis(BaseModel):
    sessions: list[SessionInsight]
    unified_report: Annotated[str, BeforeValidator(lambda v: v if v else DEFAULT_ANALYSIS_REPORT)]  # LLM-generated markdown


class TemplateAnalysis(BaseModel):
    """Analysis for a single template"""

    template_id: int
    template_name: str
    topics: dict[str, TopicAnalysis]
    total_topics: int
    total_sessions: int


class KnowledgePackAnalysisData(BaseModel):
    """Analysis data for entire knowledge pack with all templates"""

    kp_id: int
    generated_at: str
    templates: list[TemplateAnalysis]


class InterviewAnalysisGenerateRequest(BaseModel):
    use_llm: bool = True
    llm_config: dict[str, Any] | None = None


class InterviewAnalysisGenerateResponse(BaseModel):
    success: bool
    message: str
    data: KnowledgePackAnalysisData | None = None
    error: str | None = None


class InterviewAnalysisGetResponse(BaseModel):
    success: bool
    message: str
    data: KnowledgePackAnalysisData | None = None
    cached: bool = False  # Whether this was from cache
    error: str | None = None
