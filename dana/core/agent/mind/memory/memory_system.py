"""
Unified memory system interface.
"""

from typing import Any

from .conversation import ConversationMemory
from .working import WorkingMemory
from .episodic import EpisodicMemory
from .semantic import SemanticMemory


class MemorySystem:
    """Unified interface to all memory types."""

    def __init__(self):
        """Initialize all memory subsystems."""
        self.conversation = ConversationMemory()
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()

    def recall(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Smart recall across all memory types.

        Args:
            query: Query string to search for
            context: Optional context to guide search

        Returns:
            Dictionary with results from relevant memory types
        """
        results = {}

        # Check working memory first (most recent/relevant)
        if self.working.has_relevant(query):
            results["working"] = self.working.recall(query)

        # Check episodic memory for similar experiences
        if context and self.episodic.has_similar(query, context):
            results["episodic"] = self.episodic.recall_similar(query, context)

        # Check semantic memory for facts
        if self.semantic.has_knowledge(query):
            results["semantic"] = self.semantic.query(query)

        # Check conversation for recent mentions
        conversation_context = self.conversation.search(query)
        if conversation_context:
            results["conversation"] = conversation_context

        return results

    def store(self, memory_type: str, key: str, value: Any, **metadata) -> None:
        """Store information in specified memory type.

        Args:
            memory_type: Type of memory ("working", "episodic", "semantic")
            key: Memory key/identifier
            value: Value to store
            **metadata: Additional metadata
        """
        if memory_type == "working":
            self.working.store(key, value, **metadata)
        elif memory_type == "episodic":
            self.episodic.store_experience(key, value, **metadata)
        elif memory_type == "semantic":
            self.semantic.store_fact(key, value, **metadata)
        elif memory_type == "conversation":
            # Conversation memory has its own interface
            pass
        else:
            raise ValueError(f"Unknown memory type: {memory_type}")

    def get_conversation_context(self, max_turns: int = 3) -> list[dict[str, Any]]:
        """Get recent conversation context.

        Args:
            max_turns: Maximum number of turns to retrieve

        Returns:
            List of recent conversation turns
        """
        return self.conversation.get_recent_turns(max_turns)

    def get_working_context(self) -> dict[str, Any]:
        """Get current working memory context.

        Returns:
            Dictionary of working memory contents
        """
        return self.working.get_all()

    def clear_working_memory(self) -> None:
        """Clear working memory for new task."""
        self.working.clear()

    def consolidate(self) -> None:
        """Consolidate memories from working to long-term storage."""
        # Get important items from working memory
        important_items = self.working.get_important()

        # Move to appropriate long-term memory
        for key, value, metadata in important_items:
            if metadata.get("type") == "experience":
                self.episodic.store_experience(key, value, **metadata)
            elif metadata.get("type") == "fact":
                self.semantic.store_fact(key, value, **metadata)

        # Clear transferred items from working memory
        self.working.clear_transferred()

    def get_status(self) -> dict[str, Any]:
        """Get memory system status.

        Returns:
            Dictionary with memory statistics
        """
        return {
            "conversation_turns": len(self.conversation.history) if hasattr(self.conversation, "history") else 0,
            "working_items": self.working.size(),
            "episodic_memories": self.episodic.count(),
            "semantic_facts": self.semantic.count(),
        }
