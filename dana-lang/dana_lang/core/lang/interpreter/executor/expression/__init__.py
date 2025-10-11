"""
Expression optimization modules for Dana language.

This package contains specialized modules for optimizing expression execution:
- IdentifierResolver: Optimized identifier resolution with caching
- CollectionProcessor: Optimized collection literal processing
- BinaryOperationHandler: Optimized arithmetic and logical operations
- PipeExecutor: Optimized function composition and pipe operations

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from .binary_operation_handler import BinaryOperationHandler
from .collection_processor import CollectionProcessor
from .identifier_resolver import IdentifierResolver

__all__ = ["IdentifierResolver", "CollectionProcessor", "BinaryOperationHandler"]
