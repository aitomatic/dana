"""
OpenDXA KNOWS - Knowledge Ingestion and Organization System

This module provides intelligent knowledge ingestion capabilities with document processing,
knowledge extraction, validation, and organization.
"""

from .core.base import Document, ParsedDocument, KnowledgePoint, Knowledge
from .core.registry import KORegistry, ko_registry
from .document.loader import DocumentLoader
from .document.parser import DocumentParser  
from .document.extractor import TextExtractor
from .extraction import (
    MetaKnowledgeExtractor, 
    KnowledgeCategorizer, 
    KnowledgeCategory, 
    CategoryRelationship,
    SimilaritySearcher,
    ContextExpander
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
    "ContextExpander"
]
