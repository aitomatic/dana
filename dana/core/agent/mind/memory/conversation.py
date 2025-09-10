"""
Conversation memory implementation for agent mind.

This module provides conversation memory capabilities that enable agents to remember
and recall past interactions with users, with JSON-based persistence and timeline integration.
"""

import json
import shutil
import uuid
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ConversationMemory:
    """Conversation memory with JSON persistence and timeline integration."""

    def __init__(self, filepath: str, max_turns: int = 20):
        """Initialize conversation memory.

        Args:
            filepath: Path to JSON file for persistence (required)
            max_turns: Maximum number of turns to keep in active memory
        """
        if not filepath:
            raise ValueError("filepath is required for ConversationMemory")

        self.filepath = Path(filepath)
        self.max_turns = max_turns

        # Initialize data structures
        self.history = deque(maxlen=max_turns)
        self.summaries = []

        # Initialize metadata
        self.metadata = {
            "session_count": 1,
            "total_turns": 0,
            "conversation_id": str(uuid.uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

        # Load existing data if file exists
        self._load()

    def add_turn(self, user_input: str, agent_response: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Add a conversation turn to memory.

        Args:
            user_input: The user's input message
            agent_response: The agent's response
            metadata: Optional metadata for this turn

        Returns:
            Dictionary containing the turn data
        """
        turn = {
            "turn_id": str(uuid.uuid4()),
            "user_input": user_input,
            "agent_response": agent_response,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": metadata or {},
        }

        self.history.append(turn)
        self.metadata["total_turns"] += 1
        self.metadata["updated_at"] = turn["timestamp"]

        # Auto-save
        self.save()

        return turn

    def get_recent_context(self, turns: int = 5) -> list[dict[str, Any]]:
        """Get recent conversation context.

        Args:
            turns: Number of recent turns to retrieve

        Returns:
            List of recent conversation turns
        """
        return list(self.history)[-turns:] if self.history else []

    def build_llm_context(self, current_query: str, task_type: str | None = None, include_summaries: bool = False) -> str:
        """Build context string for LLM interactions.

        Args:
            current_query: The current user query
            task_type: Optional task type for context customization
            include_summaries: Whether to include conversation summaries

        Returns:
            Formatted context string for LLM
        """
        context_parts = []

        # Add conversation summaries if requested
        if include_summaries and self.summaries:
            context_parts.append("Previous conversation summary:")
            for summary in self.summaries[-2:]:  # Include last 2 summaries
                context_parts.append(f"- {summary.get('content', 'No content')}")
            context_parts.append("")

        # Add recent conversation history
        if self.history:
            context_parts.append("Recent conversation:")
            recent_turns = self.get_recent_context(5)
            for turn in recent_turns:
                context_parts.append(f"User: {turn['user_input']}")
                context_parts.append(f"Agent: {turn['agent_response']}")
                context_parts.append("")

        # Add current query
        context_parts.append(f"Current user query: {current_query}")

        return "\n".join(context_parts)

    def search_history(self, query: str) -> list[dict[str, Any]]:
        """Search through conversation history.

        Args:
            query: Search query string

        Returns:
            List of matching conversation turns
        """
        query_lower = query.lower()
        matches = []

        for turn in self.history:
            if (query_lower in turn["user_input"].lower() or
                query_lower in turn["agent_response"].lower()):
                matches.append(turn)

        return matches

    def create_summary(self, start_turn: int = 0, end_turn: int = -1) -> dict[str, Any]:
        """Create a summary of conversation history.

        Args:
            start_turn: Starting turn index (0-based)
            end_turn: Ending turn index (exclusive, -1 for last turn)

        Returns:
            Summary dictionary
        """
        if not self.history:
            return {}

        history_list = list(self.history)
        if end_turn == -1:
            end_turn = len(history_list)

        # Calculate turn count (end_turn is exclusive)
        turn_count = end_turn - start_turn

        summary = {
            "summary_id": str(uuid.uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "turn_count": turn_count,
            "start_turn": start_turn,
            "end_turn": end_turn,
            "content": f"Summary of {turn_count} conversation turns",
        }

        self.summaries.append(summary)
        return summary

    def get_statistics(self) -> dict[str, Any]:
        """Get conversation statistics.

        Returns:
            Dictionary containing conversation statistics
        """
        return {
            "total_turns": self.metadata["total_turns"],
            "active_turns": len(self.history),
            "summary_count": len(self.summaries),
            "session_count": self.metadata["session_count"],
            "conversation_id": self.metadata["conversation_id"],
            "created_at": self.metadata["created_at"],
            "updated_at": self.metadata["updated_at"],
        }

    def clear(self) -> None:
        """Clear conversation memory."""
        self.history.clear()
        self.summaries.clear()
        self.metadata["total_turns"] = 0
        self.metadata["session_count"] = 1  # Reset to 1, not increment
        self.metadata["updated_at"] = datetime.now(UTC).isoformat()
        self.save()

    def save(self, backup: bool = True) -> None:
        """Save conversation memory to disk.

        Args:
            backup: Whether to create a backup before saving
        """
        try:
            # Create backup if requested and file exists
            if backup and self.filepath.exists():
                backup_path = self.filepath.with_suffix(".json.bak")
                shutil.copy2(self.filepath, backup_path)

            # Prepare data for serialization
            data = {
                "conversation_id": self.metadata["conversation_id"],
                "created_at": self.metadata["created_at"],
                "updated_at": self.metadata["updated_at"],
                "history": list(self.history),
                "summaries": self.summaries,
                "metadata": self.metadata,
            }

            # Ensure directory exists
            self.filepath.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first (atomic write)
            temp_path = self.filepath.with_suffix(".json.tmp")
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)

            # Move temp file to final location (atomic on most systems)
            temp_path.replace(self.filepath)

        except Exception as e:
            print(f"Warning: Failed to save conversation memory: {e}")

    def _load(self) -> bool:
        """Load conversation memory from disk.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.filepath.exists():
            return False

        try:
            with open(self.filepath) as f:
                data = json.load(f)

            # Restore metadata
            self.metadata.update(data.get("metadata", {}))

            # Restore history
            history_data = data.get("history", [])
            self.history = deque(history_data, maxlen=self.max_turns)

            # Restore summaries
            self.summaries = data.get("summaries", [])

            # Update session count
            self.metadata["session_count"] = self.metadata.get("session_count", 0) + 1

            return True

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Failed to load conversation memory: {e}")
            # Try to load backup if available
            backup_path = self.filepath.with_suffix(".json.bak")
            if backup_path.exists():
                shutil.copy2(backup_path, self.filepath)
                return self._load()  # Recursive call to load backup
            return False
