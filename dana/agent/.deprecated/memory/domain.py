import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    FACT = "fact"
    EVENT = "event"
    PROCEDURE = "procedure"
    OPINION = "opinion"
    TOPIC = "topic"


class ShareLevel(Enum):
    PUBLIC = "public"
    ANONYMOUS = "anonymous"
    COMMUNITY = "community"


class MemoryStatus(Enum):
    ACTIVATED = "activated"
    ARCHIVED = "archived"
    DELETED = "deleted"


class StorageType(Enum):
    WORKING_MEMORY = "WorkingMemory"
    LONG_TERM_MEMORY = "LongTermMemory"
    USER_MEMORY = "UserMemory"


@dataclass
class MemoryMetadata:
    memory_type: StorageType
    key: str | None = None
    tags: list[str] = field(default_factory=list)
    embedding: list[float] | None = None
    confidence: float | None = None
    entities: list[str] = field(default_factory=list)
    type: MemoryType = MemoryType.FACT
    status: MemoryStatus = MemoryStatus.ACTIVATED


def _default_metadata() -> MemoryMetadata:
    return MemoryMetadata(memory_type=StorageType.WORKING_MEMORY)


@dataclass
class MemoryItem:
    memory: str  # The actual memory content (following MemOS naming)
    user_id: str
    timestamp: datetime
    session_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: MemoryMetadata = field(default_factory=_default_metadata)

    # Legacy compatibility properties
    @property
    def content(self) -> str:
        return self.memory

    @property
    def embedding(self) -> list[float] | None:
        return self.metadata.embedding

    @property
    def memory_type(self) -> MemoryType:
        return self.metadata.type

    @property
    def confidence(self) -> float | None:
        return self.metadata.confidence


class MemoryUnit:
    """Domain model for memory containers"""

    def __init__(self, unit_id: str, user_id: str, name: str):
        self.unit_id = unit_id
        self.user_id = user_id
        self.name = name
        self.memories: list[MemoryItem] = []

    def add_memory(self, memory: MemoryItem, target_type: str | None = None):
        # Optionally, target_type can be used for further classification
        self.memories.append(memory)

    def get_all_memories(self) -> list[MemoryItem]:
        return self.memories
