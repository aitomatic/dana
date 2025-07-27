"""
This module provides document processing capabilities for the KNOWS framework.

It includes tools for:
- Loading documents from various sources (`DocumentLoader`).
- Parsing document structures and metadata (`DocumentParser`).
- Extracting text content from documents (`TextExtractor`).

These components work together to facilitate efficient document analysis and processing.
"""

from .extractor import TextExtractor
from .loader import DocumentLoader
from .parser import DocumentParser

__all__ = ["TextExtractor", "DocumentLoader", "DocumentParser"]
