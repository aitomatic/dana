from __future__ import annotations
from pydantic import BaseModel

# Base response schema for common API response pattern


class BaseAPIResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None
