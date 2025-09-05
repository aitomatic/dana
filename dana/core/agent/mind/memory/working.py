"""
Working memory for current task context.
"""

from datetime import datetime
from typing import Any


class WorkingMemory:
    """Working memory for current task context and temporary information."""

    def __init__(self, max_items: int = 100):
        """Initialize working memory.

        Args:
            max_items: Maximum number of items to keep
        """
        self.max_items = max_items
        self._memory: dict[str, dict[str, Any]] = {}
        self._access_counts: dict[str, int] = {}
        self._importance: dict[str, float] = {}
        self._transferred: set[str] = set()

    def store(self, key: str, value: Any, importance: float = 0.5, **metadata) -> None:
        """Store item in working memory.

        Args:
            key: Item key
            value: Item value
            importance: Importance score (0.0 to 1.0)
            **metadata: Additional metadata
        """
        # Enforce size limit
        if len(self._memory) >= self.max_items and key not in self._memory:
            self._evict_least_important()

        self._memory[key] = {
            "value": value,
            "timestamp": datetime.now(),
            "metadata": metadata,
        }
        self._importance[key] = importance
        self._access_counts[key] = 0

    def recall(self, key: str) -> Any:
        """Recall item from working memory.

        Args:
            key: Item key

        Returns:
            Item value or None if not found
        """
        if key in self._memory:
            self._access_counts[key] += 1
            return self._memory[key]["value"]
        return None

    def has_relevant(self, query: str) -> bool:
        """Check if working memory has relevant information.

        Args:
            query: Query string

        Returns:
            True if relevant information found
        """
        query_lower = query.lower()
        for key in self._memory:
            if query_lower in key.lower():
                return True
        return False

    def search(self, query: str) -> dict[str, Any]:
        """Search working memory for relevant items.

        Args:
            query: Search query

        Returns:
            Dictionary of matching items
        """
        query_lower = query.lower()
        results = {}

        for key, item in self._memory.items():
            if query_lower in key.lower():
                results[key] = item["value"]
            elif "tags" in item["metadata"]:
                if any(query_lower in tag.lower() for tag in item["metadata"]["tags"]):
                    results[key] = item["value"]

        return results

    def get_all(self) -> dict[str, Any]:
        """Get all items in working memory.

        Returns:
            Dictionary of all items
        """
        return {key: item["value"] for key, item in self._memory.items()}

    def get_important(self, threshold: float = 0.7) -> list[tuple[str, Any, dict]]:
        """Get important items for consolidation.

        Args:
            threshold: Importance threshold

        Returns:
            List of (key, value, metadata) tuples
        """
        important = []

        for key, importance in self._importance.items():
            if importance >= threshold and key not in self._transferred:
                item = self._memory[key]
                important.append((key, item["value"], item["metadata"]))

        return important

    def clear(self) -> None:
        """Clear all working memory."""
        self._memory.clear()
        self._access_counts.clear()
        self._importance.clear()
        self._transferred.clear()

    def clear_transferred(self) -> None:
        """Clear items that have been transferred to long-term memory."""
        for key in self._transferred:
            if key in self._memory:
                del self._memory[key]
                del self._access_counts[key]
                del self._importance[key]
        self._transferred.clear()

    def mark_transferred(self, key: str) -> None:
        """Mark an item as transferred to long-term memory.

        Args:
            key: Item key
        """
        self._transferred.add(key)

    def size(self) -> int:
        """Get number of items in working memory.

        Returns:
            Number of items
        """
        return len(self._memory)

    def _evict_least_important(self) -> None:
        """Evict least important item when memory is full."""
        if not self._memory:
            return

        # Calculate scores combining importance and access frequency
        scores = {}
        for key in self._memory:
            importance = self._importance.get(key, 0.5)
            accesses = self._access_counts.get(key, 0)
            # Combine importance and access frequency
            scores[key] = importance * 0.7 + min(accesses / 10, 1.0) * 0.3

        # Find and evict item with lowest score
        min_key = min(scores, key=scores.get)
        del self._memory[min_key]
        del self._access_counts[min_key]
        del self._importance[min_key]
        if min_key in self._transferred:
            self._transferred.remove(min_key)
