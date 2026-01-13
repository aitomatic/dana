from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import StrEnum


class BackgroundTaskStatus(StrEnum):
    """Status values for background tasks."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BackgroundTaskType(StrEnum):
    """Task type values for background tasks."""

    KNOWLEDGE_GEN = "knowledge_gen"
    DEEP_EXTRACT = "deep_extract"


class BackgroundTaskResponse(BaseModel):
    id: int
    type: str
    status: BackgroundTaskStatus
    data: dict = {}
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(use_enum_values=True)
