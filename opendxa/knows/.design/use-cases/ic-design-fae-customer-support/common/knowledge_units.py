"""
Knowledge Units and P-T Classification System

Defines the core data structures for KNOWS knowledge management.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class Phase(Enum):
    """Knowledge phase - when knowledge became real."""

    PRIOR = "Prior"
    DOCUMENTARY = "Documentary"
    EXPERIENTIAL = "Experiential"


class Type(Enum):
    """Knowledge type - what kind of knowledge."""

    TOPICAL = "Topical"
    PROCEDURAL = "Procedural"


class SourceType(Enum):
    """Knowledge source type."""

    HUMAN = "Human"
    MACHINE = "Machine"
    DOCUMENT = "Document"
    GENERATED = "Generated"
    COMPUTED = "Computed"


@dataclass
class P_T_Classification:
    """P-T classification for knowledge units."""

    phase: Phase
    type: Type

    def __str__(self):
        return f"{self.phase.value} + {self.type.value}"


@dataclass
class KnowledgeUnit:
    """Atomic unit of knowledge in KNOWS."""

    id: str
    content: str
    p_t_classification: P_T_Classification
    source_type: SourceType
    source_authority: float  # 0-1
    confidence: float  # 0-1
    scope: list[str]
    status: str  # raw, validated, archived
    usage_count: int
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any]

    def __post_init__(self):
        """Validate knowledge unit after initialization."""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if not 0 <= self.source_authority <= 1:
            raise ValueError("Source authority must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        """Convert knowledge unit to dictionary for storage."""
        return {
            "id": self.id,
            "content": self.content,
            "phase": self.p_t_classification.phase.value,
            "type": self.p_t_classification.type.value,
            "source_type": self.source_type.value,
            "source_authority": self.source_authority,
            "confidence": self.confidence,
            "scope": self.scope,
            "status": self.status,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeUnit":
        """Create knowledge unit from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            p_t_classification=P_T_Classification(phase=Phase(data["phase"]), type=Type(data["type"])),
            source_type=SourceType(data["source_type"]),
            source_authority=data["source_authority"],
            confidence=data["confidence"],
            scope=data["scope"],
            status=data["status"],
            usage_count=data["usage_count"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data["metadata"],
        )

    def increment_usage(self):
        """Increment usage count and update timestamp."""
        self.usage_count += 1
        self.updated_at = datetime.now()

    def update_confidence(self, new_confidence: float):
        """Update confidence score."""
        if not 0 <= new_confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        self.confidence = new_confidence
        self.updated_at = datetime.now()

    def promote_status(self, new_status: str):
        """Promote knowledge unit status."""
        valid_statuses = ["raw", "validated", "archived"]
        if new_status not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        self.status = new_status
        self.updated_at = datetime.now()
