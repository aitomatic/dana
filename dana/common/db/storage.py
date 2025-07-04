"""
Storage implementations for the Dana system.

This module provides the mapping between Memory/Knowledge (logical) and
SQL/Vector (physical) storage mechanisms. In Dana, Memories are stored in
vector databases, while Knowledge is stored in SQL databases.

This is because Memories are accessed via semantic search. Knowledge bases, on the other hand,
are accessed via Capabilities and other keywords.
"""

from typing import TypeVar

from dana.common.db.base_storage import SqlDBStorage, VectorDBStorage
from dana.common.db.models import KnowledgeDBModel, MemoryDBModel

M = TypeVar("M", bound=MemoryDBModel)


class KnowledgeDBStorage(SqlDBStorage[KnowledgeDBModel]):
    """Storage for knowledge base entries."""

    def __init__(self, connection_string: str):
        # Initialize the parent SqlDBStorage with KnowledgeDBModel.
        # KnowledgeDBModel defines the schema for knowledge base entries,
        # which are stored in SQL databases. This ensures that the storage
        # mechanism is correctly configured for handling knowledge data.
        super().__init__(connection_string, KnowledgeDBModel)


class MemoryDBStorage(VectorDBStorage[M]):
    """Storage for memory entries."""

    def __init__(self, vector_db_url: str, embedding_model, memory_model_class: type[M]):
        """Initialize memory storage.

        Args:
            vector_db_url: Vector database connection URL
            embedding_model: Model to generate embeddings
            memory_model_class: The memory model class to use
        """
        super().__init__(vector_db_url, embedding_model, memory_model_class)
