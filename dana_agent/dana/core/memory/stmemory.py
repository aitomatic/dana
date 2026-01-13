"""
Short-term memory for session timeline tracking.

STMemory maintains a bounded timeline of session events (user messages,
agent responses, observations, etc.) with automatic size management.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemoryEntry:
    """Single memory entry in the timeline."""

    role: str  # user, agent, observation, system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class STMemory:
    """Short-term session memory.

    Maintains a timeline of session events with configurable size limit.
    When the limit is exceeded, oldest entries are dropped.
    """

    def __init__(self, max_entries: int = 1000):
        """
        Initialize STMemory.

        Args:
            max_entries: Maximum number of entries to retain (default: 1000)
        """
        self.max_entries = max_entries
        self.entries: list[MemoryEntry] = []

    def append(self, role: str, content: str) -> None:
        """
        Add entry to timeline with auto-timestamp.

        Drops oldest entry if over limit.

        Args:
            role: Entry role (user, agent, observation, system)
            content: Entry content
        """
        entry = MemoryEntry(role=role, content=content)
        self.entries.append(entry)

        # Drop oldest if over limit
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)

    def recent(self, n: int = 10) -> list[MemoryEntry]:
        """
        Get n most recent entries.

        Args:
            n: Number of entries to return

        Returns:
            List of most recent MemoryEntry objects
        """
        return self.entries[-n:]

    @property
    def timeline(self) -> list[MemoryEntry]:
        """Full timeline of all entries."""
        return self.entries

    def estimate_tokens(self) -> int:
        """
        Estimate token count for context building.

        Uses rough heuristic of ~4 characters per token.

        Returns:
            Estimated token count
        """
        total_chars = sum(len(e.content) + len(e.role) + 20 for e in self.entries)
        return total_chars // 4

    def clear(self) -> None:
        """Clear all entries."""
        self.entries.clear()

    def to_text(self) -> str:
        """
        Format timeline as text for context inclusion.

        Returns:
            Formatted string representation of timeline
        """
        if not self.entries:
            return ""

        lines = []
        for entry in self.entries:
            ts = entry.timestamp.strftime("%H:%M:%S")
            lines.append(f"[{ts}] {entry.role}: {entry.content}")
        return "\n".join(lines)

    def __len__(self) -> int:
        """Return number of entries."""
        return len(self.entries)
