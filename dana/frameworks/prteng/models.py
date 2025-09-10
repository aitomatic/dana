"""
Data models for the PromptEngineer framework.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any


@dataclass
class Prompt:
    """Represents a generated prompt with UUID tracking."""

    id: str
    system_message: str | None = None
    user_message: str = ""

    def __post_init__(self):
        """Validate that ID is not empty."""
        if not self.id or not self.id.strip():
            raise ValueError("Prompt ID cannot be empty")

    @property
    def text(self) -> str:
        """Get the full conversation text combining system and user messages."""
        if self.system_message:
            return f"System: {self.system_message}\n\nUser: {self.user_message}"
        else:
            return self.user_message

    @text.setter
    def text(self, value: str):
        """Set the full conversation text, parsing system and user messages."""
        if value.startswith("System: ") and "\n\nUser: " in value:
            parts = value.split("\n\nUser: ", 1)
            self.system_message = parts[0][8:]  # Remove "System: " prefix
            self.user_message = parts[1]
        else:
            self.system_message = None
            self.user_message = value


@dataclass
class Interaction:
    """Record of a prompt-response-feedback cycle."""

    prompt_id: str
    response: str
    timestamp: datetime
    success_score: float
    feedback: str | None = None
    evaluation: "Evaluation | None" = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        if self.evaluation:
            data["evaluation"] = asdict(self.evaluation)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Interaction":
        """Create from dictionary loaded from JSON."""
        # Parse timestamp
        if isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Parse evaluation if present
        if data.get("evaluation"):
            data["evaluation"] = Evaluation.from_dict(data["evaluation"])

        return cls(**data)


@dataclass
class Evaluation:
    """Result of evaluating an LLM response."""

    prompt_id: str
    response: str
    criteria_scores: dict[str, float]  # clarity, completeness, style, etc.
    overall_score: float
    improvement_suggestions: list[str]
    confidence: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evaluation":
        """Create from dictionary loaded from JSON."""
        return cls(**data)


@dataclass
class TemplateVersion:
    """Represents a version of a template."""

    template: str
    version: int
    timestamp: datetime
    prompt_id: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {"template": self.template, "version": self.version, "timestamp": self.timestamp.isoformat(), "prompt_id": self.prompt_id}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TemplateVersion":
        """Create from dictionary loaded from JSON."""
        if isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)
