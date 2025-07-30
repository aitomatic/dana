import json
import os
import threading
import uuid
from datetime import datetime
from typing import Any

from .domain import MemoryItem, MemoryMetadata, MemoryStatus, MemoryType, StorageType
from .repository import BaseMemoryRepository


class JSONMemoryRepository(BaseMemoryRepository):
    """Base JSON repository with common file operations"""

    def __init__(self, storage_path: str, filename: str):
        self.storage_path = storage_path
        self.file_path = os.path.join(storage_path, filename)
        self._lock = threading.Lock()
        os.makedirs(storage_path, exist_ok=True)

    def _serialize_memory_item(self, memory: MemoryItem) -> dict[str, Any]:
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

    def _deserialize_memory_item(self, data: dict[str, Any]) -> MemoryItem:
        """Convert dict back to MemoryItem"""
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

    def _load_memories(self) -> list[MemoryItem]:
        """Load all memories from JSON file"""
        if not os.path.exists(self.file_path):
            return []

        try:
            with open(self.file_path, encoding="utf-8") as f:
                data = json.load(f)
                return [self._deserialize_memory_item(item) for item in data]
        except (json.JSONDecodeError, KeyError, ValueError):
            # If file is corrupted, start fresh
            return []

    def _save_memories(self, memories: list[MemoryItem]):
        """Save all memories to JSON file"""
        data = [self._serialize_memory_item(memory) for memory in memories]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _text_search(self, memories: list[MemoryItem], query: str, limit: int) -> list[MemoryItem]:
        """Simple text-based search in memory content"""
        if not query:
            return memories[:limit]

        query_lower = query.lower()
        matches = []

        for memory in memories:
            score = 0
            content_lower = memory.memory.lower()

            # Direct substring match
            if query_lower in content_lower:
                score += 10

            # Word matches
            query_words = query_lower.split()
            content_words = content_lower.split()
            word_matches = sum(1 for word in query_words if word in content_words)
            score += word_matches * 2

            # Tag matches
            if memory.metadata.tags:
                tag_matches = sum(1 for tag in memory.metadata.tags if query_lower in tag.lower())
                score += tag_matches * 5

            if score > 0:
                matches.append((memory, score))

        # Sort by score (descending) and return top results
        matches.sort(key=lambda x: x[1], reverse=True)
        return [memory for memory, _ in matches[:limit]]


class JSONLongTermMemory(JSONMemoryRepository):
    """Long-term memory with semantic deduplication using JSON storage"""

    def __init__(self, user_id: str, storage_path: str = ".dana/memory"):
        user_storage = os.path.join(storage_path, user_id)
        super().__init__(user_storage, "long_term_memory.json")
        self.user_id = user_id
        self.max_items = 10000
        self.similarity_threshold = 0.85  # For deduplication

    async def store(self, memory: MemoryItem) -> bool:
        """Store memory with deduplication"""
        with self._lock:
            memories = self._load_memories()

            # Simple deduplication: check for similar content
            if self._is_duplicate(memory, memories):
                return False

            memories.append(memory)

            # Apply capacity limit (FIFO)
            if len(memories) > self.max_items:
                memories = memories[-self.max_items :]

            self._save_memories(memories)
            return True

    async def search(self, query_embedding: list[float], limit: int) -> list[MemoryItem]:
        """Search memories (text-based for now, embedding parameter kept for interface compatibility)"""
        with self._lock:
            memories = self._load_memories()
            # Since we don't have vector search yet, use text search
            # Convert embedding to text if needed (for now, return recent items)
            return memories[-limit:] if memories else []

    async def search_by_text(self, query: str, limit: int = 10) -> list[MemoryItem]:
        """Text-based search method"""
        with self._lock:
            memories = self._load_memories()
            return self._text_search(memories, query, limit)

    async def retrieve(self, memory_id: str) -> MemoryItem | None:
        """Retrieve specific memory by ID"""
        with self._lock:
            memories = self._load_memories()
            for memory in memories:
                if memory.id == memory_id:
                    return memory
            return None

    def _is_duplicate(self, new_memory: MemoryItem, existing_memories: list[MemoryItem]) -> bool:
        """Simple text-based deduplication"""
        new_content = new_memory.memory.lower().strip()

        for existing in existing_memories[-100:]:  # Check last 100 items
            existing_content = existing.memory.lower().strip()

            # Exact match
            if new_content == existing_content:
                return True

            # Similar content (simple Jaccard similarity)
            new_words = set(new_content.split())
            existing_words = set(existing_content.split())

            if new_words and existing_words:
                intersection = len(new_words & existing_words)
                union = len(new_words | existing_words)
                similarity = intersection / union if union > 0 else 0

                if similarity > self.similarity_threshold:
                    return True

        return False


class JSONUserMemory(JSONMemoryRepository):
    """User memory for personal preferences and profile data using JSON storage"""

    def __init__(self, user_id: str, storage_path: str = ".dana/memory"):
        user_storage = os.path.join(storage_path, user_id)
        super().__init__(user_storage, "user_memory.json")
        self.user_id = user_id

    async def store(self, memory: MemoryItem) -> bool:
        """Store user memory (unlimited capacity)"""
        with self._lock:
            memories = self._load_memories()
            memories.append(memory)
            self._save_memories(memories)
            return True

    async def search(self, query_embedding: list[float], limit: int) -> list[MemoryItem]:
        """Search user memories"""
        with self._lock:
            memories = self._load_memories()
            return memories[-limit:] if memories else []

    async def search_by_text(self, query: str, limit: int = 10) -> list[MemoryItem]:
        """Text-based search for user memories"""
        with self._lock:
            memories = self._load_memories()
            return self._text_search(memories, query, limit)

    async def retrieve(self, memory_id: str) -> MemoryItem | None:
        """Retrieve specific memory by ID"""
        with self._lock:
            memories = self._load_memories()
            for memory in memories:
                if memory.id == memory_id:
                    return memory
            return None

    async def get_user_profile_summary(self) -> dict[str, Any]:
        """Generate a summary of user preferences and characteristics"""
        with self._lock:
            memories = self._load_memories()

            # Categorize memories
            preferences = []
            facts = []
            topics = []

            for memory in memories:
                if memory.metadata.type == MemoryType.OPINION:
                    preferences.append(memory.memory)
                elif memory.metadata.type == MemoryType.FACT:
                    facts.append(memory.memory)
                elif memory.metadata.type == MemoryType.TOPIC:
                    topics.append(memory.memory)

            return {
                "user_id": self.user_id,
                "total_memories": len(memories),
                "preferences": preferences[-10:],  # Last 10 preferences
                "facts": facts[-10:],  # Last 10 facts
                "topics": topics[-10:],  # Last 10 topics
                "memory_types": {"preferences": len(preferences), "facts": len(facts), "topics": len(topics)},
            }


class JSONSharedMemory(JSONMemoryRepository):
    """Shared memory for collective knowledge using JSON storage"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, storage_path: str = ".dana/memory"):
        """Singleton pattern for shared memory"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, storage_path: str = ".dana/memory"):
        if not hasattr(self, "initialized"):
            super().__init__(storage_path, "shared_memory.json")
            self.max_items = 50000
            self.initialized = True

    async def store(self, memory: MemoryItem) -> bool:
        """Store shared memory with privacy filtering"""
        if not self._should_share(memory):
            return False

        with self._lock:
            memories = self._load_memories()

            # Remove personal information
            sanitized_memory = self._sanitize_memory(memory)
            memories.append(sanitized_memory)

            # Apply capacity limit (FIFO)
            if len(memories) > self.max_items:
                memories = memories[-self.max_items :]

            self._save_memories(memories)
            return True

    async def search(self, query_embedding: list[float], limit: int) -> list[MemoryItem]:
        """Search shared memories"""
        with self._lock:
            memories = self._load_memories()
            return memories[-limit:] if memories else []

    async def search_by_text(self, query: str, limit: int = 10) -> list[MemoryItem]:
        """Text-based search for shared memories"""
        with self._lock:
            memories = self._load_memories()
            return self._text_search(memories, query, limit)

    async def retrieve(self, memory_id: str) -> MemoryItem | None:
        """Retrieve specific memory by ID"""
        with self._lock:
            memories = self._load_memories()
            for memory in memories:
                if memory.id == memory_id:
                    return memory
            return None

    def _should_share(self, memory: MemoryItem) -> bool:
        """Determine if memory should be shared (privacy filter)"""
        content_lower = memory.memory.lower()

        # Don't share personal information
        personal_indicators = [
            "my name is",
            "i am",
            "i live",
            "my address",
            "my phone",
            "my email",
            "password",
            "secret",
            "personal",
            "private",
            "confidential",
        ]

        for indicator in personal_indicators:
            if indicator in content_lower:
                return False

        # Only share facts and procedures with high confidence
        if memory.metadata.type in [MemoryType.FACT, MemoryType.PROCEDURE]:
            return memory.metadata.confidence is not None and memory.metadata.confidence > 0.8

        return False

    def _sanitize_memory(self, memory: MemoryItem) -> MemoryItem:
        """Remove or anonymize personal information from memory"""
        # Create a copy with anonymized user info
        sanitized = MemoryItem(
            id=str(uuid.uuid4()),  # New ID for shared memory
            memory=memory.memory,
            user_id="anonymous",  # Anonymize user
            session_id=None,  # Remove session info
            timestamp=memory.timestamp,
            metadata=memory.metadata,
        )
        return sanitized

    async def get_collective_stats(self) -> dict[str, Any]:
        """Get statistics about shared knowledge"""
        with self._lock:
            memories = self._load_memories()

            memory_types = {}
            for memory in memories:
                mem_type = memory.metadata.type.value
                memory_types[mem_type] = memory_types.get(mem_type, 0) + 1

            return {"total_shared_memories": len(memories), "memory_types": memory_types, "storage_path": self.file_path}
