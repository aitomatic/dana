"""
Storage implementations for the OpenDXA system.

This module provides the mapping between Memory/Knowledge (logical) and
SQL/Vector (physical) storage mechanisms. In OpenDXA, Memories are stored in
vector databases, while Knowledge is stored in SQL databases.

This is because Memories are accessed via semantic search. Knowledge bases, on the other hand,
are accessed via Capabilities and other keywords.
"""

from typing import TypeVar
from opendxa.common.db.storage import SqlDBStorage, VectorDBStorage
from opendxa.base.db import KnowledgeDBModel, MemoryDBModel

M = TypeVar('M', bound=MemoryDBModel)

class KnowledgeDBStorage(SqlDBStorage[KnowledgeDBModel]):
    """Storage for knowledge base entries."""
    def __init__(self, connection_string: str):
        # Initialize the parent SqlDBStorage with KnowledgeDBModel.
        # KnowledgeDBModel defines the schema for knowledge base entries,
        # which are stored in SQL databases. This ensures that the storage
        # mechanism is correctly configured for handling knowledge data.
        super().__init__(KnowledgeDBModel, connection_string)
class MemoryDBStorage(VectorDBStorage[M]):
    """Storage for memory entries."""
