"""Database storage implementations for the OpenDXA system.

Here we provide the model-to-storage mappings for the OpenDXA memory and knowledge
subsystems: Memories are stored in vector databases, while Knowledge is stored in SQL databases.

This is because Memories are accessed via semantic search, while Knowledge is accessed via
Capabilities and other keywords.

At this level, we do not distinguish between different types of Memories (ST, LT, Permanent),
as they all use the same vector DB storage. That is handled at the Resource level.
"""

from opendxa.common.db.models import (
    BaseDBModel,
    KnowledgeDBModel,
    MemoryDBModel,
)

from opendxa.common.db.storage import (
    SqlDBStorage,
    VectorDBStorage
)

__all__ = [
    # Models
    'BaseDBModel',
    'KnowledgeDBModel',
    'MemoryDBModel',
    
    # Storage
    'SqlDBStorage',
    'VectorDBStorage',
] 