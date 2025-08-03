import threading
import json
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime

from .domain import MemoryItem, MemoryMetadata, MemoryType, StorageType, MemoryStatus


class BaseMemoryRepository(ABC):
    @abstractmethod
    async def store(self, memory: MemoryItem) -> bool:
        pass

    @abstractmethod
    async def search(self, query_embedding: list[float], limit: int) -> list[MemoryItem]:
        pass

    @abstractmethod
    async def retrieve(self, memory_id: str) -> MemoryItem | None:
        pass


class WorkingMemory(BaseMemoryRepository):
    """FIFO (50 items), Session-bound, User-isolated, Persistent file-based storage"""

    def __init__(self, user_id: str, session_id: str, agent_id: str, instance_id: str, max_items: int = 50, storage_path: str = ".dana"):
        self.user_id = user_id
        self.session_id = session_id
        self.agent_id = agent_id
        self.instance_id = instance_id
        self.max_items = max_items
        self.storage_path = storage_path
        self._memories: list[MemoryItem] = []
        self._lock = threading.Lock()

        # Create storage directory and load existing memories
        self._storage_file = self._get_storage_file_path()
        self._load_memories()

    def _get_storage_file_path(self) -> Path:
        """Get the storage file path: user_id/agent_id/session_id/instance_id/working_memory.json"""
        storage_dir = Path(self.storage_path) / "agent_context_memory" / self.user_id / self.agent_id / self.session_id / self.instance_id
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "working_memory.json"

    def _load_memories(self):
        """Load memories from persistent storage"""
        try:
            if self._storage_file.exists():
                with open(self._storage_file) as f:
                    data = json.load(f)
                    for item_data in data.get("memories", []):
                        memory_item = self._deserialize_memory(item_data)
                        if memory_item:
                            self._memories.append(memory_item)
        except Exception as e:
            print(f"Warning: Could not load WorkingMemory from {self._storage_file}: {e}")

    def _save_memories(self):
        """Save memories to persistent storage"""
        try:
            data = {
                "user_id": self.user_id,
                "session_id": self.session_id,
                "agent_id": self.agent_id,
                "instance_id": self.instance_id,
                "max_items": self.max_items,
                "timestamp": datetime.now().isoformat(),
                "memories": [self._serialize_memory(memory) for memory in self._memories],
            }
            with open(self._storage_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save WorkingMemory to {self._storage_file}: {e}")

    def _serialize_memory(self, memory: MemoryItem) -> dict:
        """Convert MemoryItem to JSON-serializable dict"""
        return {
            "id": memory.id,
            "memory": memory.memory,
            "user_id": memory.user_id,
            "session_id": memory.session_id,
            "timestamp": memory.timestamp.isoformat(),
            "metadata": {
                "memory_type": memory.metadata.memory_type.value,
                "key": memory.metadata.key,
                "tags": memory.metadata.tags,
                "embedding": memory.metadata.embedding,
                "confidence": memory.metadata.confidence,
                "entities": memory.metadata.entities,
                "type": memory.metadata.type.value,
                "status": memory.metadata.status.value,
            },
        }

    def _deserialize_memory(self, data: dict) -> MemoryItem | None:
        """Convert JSON dict back to MemoryItem"""
        try:
            metadata = MemoryMetadata(
                memory_type=StorageType(data["metadata"]["memory_type"]),
                key=data["metadata"]["key"],
                tags=data["metadata"]["tags"],
                embedding=data["metadata"]["embedding"],
                confidence=data["metadata"]["confidence"],
                entities=data["metadata"]["entities"],
                type=MemoryType(data["metadata"]["type"]),
                status=MemoryStatus(data["metadata"]["status"]),
            )

            return MemoryItem(
                id=data["id"],
                memory=data["memory"],
                user_id=data["user_id"],
                session_id=data["session_id"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
                metadata=metadata,
            )
        except Exception as e:
            print(f"Warning: Could not deserialize memory item: {e}")
            return None

    async def store(self, memory: MemoryItem) -> bool:
        with self._lock:
            if len(self._memories) >= self.max_items:
                self._memories.pop(0)
            self._memories.append(memory)
            self._save_memories()
        return True

    async def search(self, query_embedding: list[float], limit: int) -> list[MemoryItem]:
        # Return most recent N memories
        with self._lock:
            return self._memories[-limit:] if limit > 0 else self._memories.copy()

    async def retrieve(self, memory_id: str) -> MemoryItem | None:
        with self._lock:
            for m in self._memories:
                if m.id == memory_id:
                    return m
        return None

    def clear_and_keep_recent(self, keep_count: int = 10):
        """Clear working memory but keep most recent items (used during batch processing)"""
        with self._lock:
            if len(self._memories) > keep_count:
                self._memories = self._memories[-keep_count:]
                self._save_memories()

    def replace_with_items(self, items_to_keep: list):
        """Replace working memory content with specific items (used for token-based retention)"""
        with self._lock:
            self._memories = items_to_keep.copy()
            self._save_memories()


class LongTermMemory(BaseMemoryRepository):
    """Persistent, semantic dedup, User-isolated, In-memory for demo"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._memories: list[MemoryItem] = []
        self._lock = threading.Lock()

    async def store(self, memory: MemoryItem) -> bool:
        with self._lock:
            # Simple dedup: don't store if content already exists
            if any(m.content == memory.content for m in self._memories):
                return False
            self._memories.append(memory)
        return True

    async def search(self, query_embedding: list[float], limit: int) -> list[MemoryItem]:
        # For demo: return most recent N
        with self._lock:
            return self._memories[-limit:]

    async def retrieve(self, memory_id: str) -> MemoryItem | None:
        with self._lock:
            for m in self._memories:
                if m.id == memory_id:
                    return m
        return None


class UserMemory(BaseMemoryRepository):
    """Unlimited, Permanent profile, User-isolated, In-memory for demo"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._memories: list[MemoryItem] = []
        self._lock = threading.Lock()

    async def store(self, memory: MemoryItem) -> bool:
        with self._lock:
            self._memories.append(memory)
        return True

    async def search(self, query_embedding: list[float], limit: int) -> list[MemoryItem]:
        with self._lock:
            return self._memories[-limit:]

    async def retrieve(self, memory_id: str) -> MemoryItem | None:
        with self._lock:
            for m in self._memories:
                if m.id == memory_id:
                    return m
        return None


class SharedMemory(BaseMemoryRepository):
    """Collective (50K), Cross-user persistent, Privacy-controlled, In-memory for demo"""

    _shared_memories: list[MemoryItem] = []
    _lock = threading.Lock()
    _max_items = 50000

    def __init__(self):
        pass

    async def store(self, memory: MemoryItem) -> bool:
        with SharedMemory._lock:
            if len(SharedMemory._shared_memories) >= SharedMemory._max_items:
                SharedMemory._shared_memories.pop(0)
            SharedMemory._shared_memories.append(memory)
        return True

    async def search(self, query_embedding: list[float], limit: int) -> list[MemoryItem]:
        with SharedMemory._lock:
            return SharedMemory._shared_memories[-limit:]

    async def retrieve(self, memory_id: str) -> MemoryItem | None:
        with SharedMemory._lock:
            for m in SharedMemory._shared_memories:
                if m.id == memory_id:
                    return m
        return None
