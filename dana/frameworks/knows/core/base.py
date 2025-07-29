"""
Base classes and interfaces for Dana KNOWS system.

This module defines the fundamental abstractions used throughout the knowledge ingestion system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Document:
    """Represents a document to be processed for knowledge extraction."""

    id: str
    source: str
    content: str
    format: str
    metadata: dict[str, Any]
    created_at: datetime

    def __post_init__(self):
        """Validate document fields after initialization."""
        if not self.id:
            raise ValueError("Document ID cannot be empty")
        if not self.content:
            raise ValueError("Document content cannot be empty")
        if self.format not in ["txt", "md", "pdf", "json", "csv"]:
            raise ValueError(f"Unsupported document format: {self.format}")


@dataclass
class ParsedDocument:
    """Represents a parsed document with extracted structure."""

    document: Document
    text_content: str
    structured_data: dict[str, Any]
    metadata: dict[str, Any]


@dataclass
class KnowledgePoint:
    """Meta-level knowledge point extracted from documents."""

    id: str
    type: str
    content: str
    context: dict[str, Any]
    confidence: float
    metadata: dict[str, Any]

    def __post_init__(self):
        """Validate knowledge point fields."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class ExpandedKnowledge:
    """Knowledge with expanded context from similarity search."""

    knowledge: KnowledgePoint
    context: list[str]
    relationships: list[dict[str, Any]]
    confidence: float


@dataclass
class ValidationResult:
    """Result of knowledge validation process."""

    is_valid: bool
    confidence: float
    issues: list[str]
    suggestions: list[str]
    metadata: dict[str, Any]


@dataclass
class Knowledge:
    """Final extracted and validated knowledge."""

    id: str
    content: str
    type: str
    context: dict[str, Any]
    validation: ValidationResult
    metadata: dict[str, Any]


class DocumentBase(ABC):
    """Abstract base class for document-related operations."""

    @abstractmethod
    def load_document(self, source: str) -> Document:
        """Load document from source."""
        pass

    @abstractmethod
    def validate_document(self, document: Document) -> bool:
        """Validate document format and content."""
        pass


class ProcessorBase(ABC):
    """Abstract base class for processing operations."""

    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Process input data and return result."""
        pass

    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data before processing."""
        pass


class KnowledgeBase(ABC):
    """Abstract base class for knowledge operations."""

    @abstractmethod
    def extract_knowledge(self, document: Document) -> list[KnowledgePoint]:
        """Extract knowledge points from document."""
        pass

    @abstractmethod
    def validate_knowledge(self, knowledge: KnowledgePoint) -> ValidationResult:
        """Validate extracted knowledge."""
        pass
