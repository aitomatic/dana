"""
Dana KNOWS - Knowledge Organization and Extraction System

This module provides intelligent knowledge ingestion capabilities with document processing,
knowledge extraction, validation, and organization.
"""

from .core.base import Document, KnowledgePoint
from .document.extractor import TextExtractor
from .document.loader import DocumentLoader
from .document.parser import DocumentParser
from .extraction import (
    CategoryRelationship,
    ContextExpander,
    KnowledgeCategorizer,
    KnowledgeCategory,
    MetaKnowledgeExtractor,
    SimilaritySearcher,
)

__version__ = "0.1.0"

__all__ = [
    # Core components
    "ProcessorBase",
    "KnowledgePoint",
    # Document processing components
    "DocumentLoader",
    "DocumentParser",
    "TextExtractor",
    "Document",
    # Meta extraction components
    "MetaKnowledgeExtractor",
    "KnowledgeCategorizer",
    "KnowledgeCategory",
    "CategoryRelationship",
    # Context expansion components
    "SimilaritySearcher",
    "ContextExpander",
]
