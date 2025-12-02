from enum import Enum
from pydantic import BaseModel


class PromptCategory(str, Enum):
    """Categories of prompts in the system."""

    TEMPLATE_GENERATION = "template_generation"
    INTERVIEW_SYSTEM = "interview_system"
    DOCUMENT_EXPLORATION = "document_exploration"
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"
    TEMPLATE_FINETUNE = "template_finetune"
    TEMPLATE_MODIFICATION = "template_modification"


class PromptSetting(BaseModel):
    """A single prompt setting with metadata."""

    category: str
    key: str
    full_key: str  # category.key
    value: str | None = None
    name: str
    description: str
    placeholders: list[str] = []
    placeholder_examples: dict[str, str] = {}  # Maps placeholder to example value
    default_value: str | None = None
    applies_to: str = "global"
    is_active: bool = True


class PromptSettingsResponse(BaseModel):
    """Response containing all prompt settings organized by category."""

    settings: dict[str, list[PromptSetting]]  # category -> [settings]
    categories: list[str]


class PromptUpdateRequest(BaseModel):
    """Request to update a prompt setting."""

    value: str
    name: str | None = None
    description: str | None = None
