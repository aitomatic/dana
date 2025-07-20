"""
Context Engine - Knowledge Curation and Context Integration

This module implements the ContextEngine for Phase 1 of the Dana Workflows framework.
Provides basic knowledge curation and context integration capabilities as the foundation
for more advanced Context Engineering in Phase 3.

Key Features:
- Simple knowledge point storage and retrieval
- Basic context integration patterns
- Foundation for KNOWS integration
- Lightweight memory management
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class KnowledgePoint:
    """Basic knowledge point for context storage."""

    id: str
    content: str
    source: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.fromisoformat(str(self.timestamp))


@dataclass
class ContextSnapshot:
    """Snapshot of context at a specific point in time."""

    id: str
    timestamp: datetime
    knowledge_points: list[KnowledgePoint]
    metadata: dict[str, Any] = field(default_factory=dict)


class ContextEngine:
    """
    Basic Context Engine for Phase 1 Foundation.

    Provides simple knowledge curation and context integration as the foundation
    for more advanced Context Engineering capabilities in Phase 3.
    """

    def __init__(self, max_knowledge_points: int = 1000):
        """
        Initialize the context engine.

        Args:
            max_knowledge_points: Maximum number of knowledge points to store
        """
        self.max_knowledge_points = max_knowledge_points
        self._knowledge_store: dict[str, KnowledgePoint] = {}
        self._context_snapshots: dict[str, ContextSnapshot] = {}
        self._tag_index: dict[str, list[str]] = {}

        logger.info(f"Initialized ContextEngine with max_knowledge_points={max_knowledge_points}")

    def add_knowledge(self, content: str, source: str, tags: list[str] | None = None, metadata: dict[str, Any] | None = None) -> str:
        """
        Add a knowledge point to the context.

        Args:
            content: The knowledge content
            source: Source identifier
            tags: Optional tags for categorization
            metadata: Optional additional metadata

        Returns:
            Knowledge point ID
        """
        knowledge_id = str(uuid.uuid4())

        knowledge_point = KnowledgePoint(
            id=knowledge_id, content=content, source=source, timestamp=datetime.now(), metadata=metadata or {}, tags=tags or []
        )

        # Store knowledge point
        self._knowledge_store[knowledge_id] = knowledge_point

        # Update tag index
        for tag in knowledge_point.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            self._tag_index[tag].append(knowledge_id)

        # Enforce max knowledge points limit
        self._enforce_limit()

        logger.debug(f"Added knowledge point {knowledge_id} from {source}")
        return knowledge_id

    def get_knowledge(self, knowledge_id: str) -> KnowledgePoint | None:
        """
        Retrieve a knowledge point by ID.

        Args:
            knowledge_id: Knowledge point ID

        Returns:
            Knowledge point or None if not found
        """
        return self._knowledge_store.get(knowledge_id)

    def find_by_tag(self, tag: str) -> list[KnowledgePoint]:
        """
        Find knowledge points by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of matching knowledge points
        """
        knowledge_ids = self._tag_index.get(tag, [])
        return [self._knowledge_store[kid] for kid in knowledge_ids if kid in self._knowledge_store]

    def search_knowledge(
        self, query: str, sources: list[str] | None = None, tags: list[str] | None = None, limit: int = 10
    ) -> list[KnowledgePoint]:
        """
        Simple search for knowledge points.

        Args:
            query: Search query string
            sources: Optional source filtering
            tags: Optional tag filtering
            limit: Maximum results to return

        Returns:
            List of matching knowledge points
        """
        results = []

        for knowledge_point in self._knowledge_store.values():
            # Check source filter
            if sources and knowledge_point.source not in sources:
                continue

            # Check tag filter
            if tags and not any(tag in knowledge_point.tags for tag in tags):
                continue

            # Simple content search
            if query.lower() in knowledge_point.content.lower():
                results.append(knowledge_point)

        # Sort by timestamp (newest first)
        results.sort(key=lambda kp: kp.timestamp, reverse=True)

        return results[:limit]

    def create_context_snapshot(self, metadata: dict[str, Any] | None = None) -> str:
        """
        Create a snapshot of the current context.

        Args:
            metadata: Optional snapshot metadata

        Returns:
            Snapshot ID
        """
        snapshot_id = str(uuid.uuid4())

        snapshot = ContextSnapshot(
            id=snapshot_id, timestamp=datetime.now(), knowledge_points=list(self._knowledge_store.values()), metadata=metadata or {}
        )

        self._context_snapshots[snapshot_id] = snapshot
        logger.debug(f"Created context snapshot {snapshot_id}")
        return snapshot_id

    def get_context_snapshot(self, snapshot_id: str) -> ContextSnapshot | None:
        """
        Retrieve a context snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Context snapshot or None if not found
        """
        return self._context_snapshots.get(snapshot_id)

    def clear_knowledge(self, source: str | None = None) -> int:
        """
        Clear knowledge points, optionally filtered by source.

        Args:
            source: Optional source filter

        Returns:
            Number of knowledge points removed
        """
        to_remove = []

        for knowledge_id, knowledge_point in self._knowledge_store.items():
            if source is None or knowledge_point.source == source:
                to_remove.append(knowledge_id)

        # Remove knowledge points
        for knowledge_id in to_remove:
            if knowledge_id in self._knowledge_store:
                knowledge_point = self._knowledge_store[knowledge_id]

                # Remove from tag index
                for tag in knowledge_point.tags:
                    if tag in self._tag_index and knowledge_id in self._tag_index[tag]:
                        self._tag_index[tag].remove(knowledge_id)
                        if not self._tag_index[tag]:
                            del self._tag_index[tag]

                del self._knowledge_store[knowledge_id]

        logger.info(f"Cleared {len(to_remove)} knowledge points")
        return len(to_remove)

    def get_stats(self) -> dict[str, Any]:
        """
        Get context engine statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_knowledge_points": len(self._knowledge_store),
            "total_snapshots": len(self._context_snapshots),
            "unique_tags": len(self._tag_index),
            "sources": list(set(kp.source for kp in self._knowledge_store.values())),
            "memory_usage": {
                "knowledge_store": len(self._knowledge_store),
                "tag_index": len(self._tag_index),
                "snapshots": len(self._context_snapshots),
            },
        }

    def _enforce_limit(self) -> None:
        """Enforce the maximum knowledge points limit."""
        if len(self._knowledge_store) > self.max_knowledge_points:
            # Remove oldest knowledge points
            sorted_knowledge = sorted(self._knowledge_store.values(), key=lambda kp: kp.timestamp)

            to_remove = len(self._knowledge_store) - self.max_knowledge_points
            for knowledge_point in sorted_knowledge[:to_remove]:
                self.clear_knowledge(knowledge_point.source)
                if len(self._knowledge_store) <= self.max_knowledge_points:
                    break

            logger.debug(f"Enforced knowledge limit, removed {to_remove} oldest points")

    def export_knowledge(self, source: str | None = None) -> dict[str, Any]:
        """
        Export knowledge points for persistence or sharing.

        Args:
            source: Optional source filter

        Returns:
            Dictionary with knowledge data
        """
        knowledge_points = []

        for knowledge_point in self._knowledge_store.values():
            if source is None or knowledge_point.source == source:
                knowledge_points.append(
                    {
                        "id": knowledge_point.id,
                        "content": knowledge_point.content,
                        "source": knowledge_point.source,
                        "timestamp": knowledge_point.timestamp.isoformat(),
                        "metadata": knowledge_point.metadata,
                        "tags": knowledge_point.tags,
                    }
                )

        return {"knowledge_points": knowledge_points, "export_timestamp": datetime.now().isoformat(), "context_engine_version": "1.0.0"}

    def import_knowledge(self, data: dict[str, Any]) -> int:
        """
        Import knowledge points from exported data.

        Args:
            data: Exported knowledge data

        Returns:
            Number of knowledge points imported
        """
        imported_count = 0

        if "knowledge_points" not in data:
            logger.warning("No knowledge points found in import data")
            return 0

        for kp_data in data["knowledge_points"]:
            try:
                knowledge_point = KnowledgePoint(
                    id=kp_data["id"],
                    content=kp_data["content"],
                    source=kp_data["source"],
                    timestamp=datetime.fromisoformat(kp_data["timestamp"]),
                    metadata=kp_data.get("metadata", {}),
                    tags=kp_data.get("tags", []),
                )

                self._knowledge_store[knowledge_point.id] = knowledge_point

                # Update tag index
                for tag in knowledge_point.tags:
                    if tag not in self._tag_index:
                        self._tag_index[tag] = []
                    if knowledge_point.id not in self._tag_index[tag]:
                        self._tag_index[tag].append(knowledge_point.id)

                imported_count += 1

            except KeyError as e:
                logger.error(f"Invalid knowledge point data: missing {e}")
                continue

        logger.info(f"Imported {imported_count} knowledge points")
        return imported_count
