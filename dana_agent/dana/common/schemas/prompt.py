from datetime import UTC, datetime

from pydantic import BaseModel, Field


class PromptVersionSnapshot(BaseModel):
    version: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    provenance: dict = Field(default_factory=dict)
    metrics: dict = Field(default_factory=dict)
