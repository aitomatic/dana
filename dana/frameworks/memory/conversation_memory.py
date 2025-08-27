"""
Conversation Memory Implementation

Provides linear conversation history with JSON persistence for context
engineering in LLM interactions.
"""

import json
import shutil
import uuid
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ConversationMemory:
    """
    Manages conversation history with configurable depth and JSON persistence.

    This class implements a simple linear memory system that:
    - Maintains recent conversation history in a deque
    - Persists conversations to JSON files
    - Provides context assembly for LLM interactions
    - Supports automatic summarization (future feature)
    """

    def __init__(self, filepath: str = "conversation_memory.json", max_turns: int = 20):
        """
        Initialize conversation memory.

        Args:
            filepath: Path to JSON file for persistence
            max_turns: Maximum number of turns to keep in active memory
        """
        self.filepath = Path(filepath)
        self.max_turns = max_turns
        self.conversation_id = str(uuid.uuid4())
        self.created_at = datetime.now(UTC).isoformat()
        self.updated_at = self.created_at

        # Use deque for efficient turn management with max size
        self.history = deque(maxlen=max_turns)
        self.summaries = []
        self.metadata = {"session_count": 1, "total_turns": 0}

        # Load existing conversation if file exists
        self.load()

    def add_turn(self, user_input: str, agent_response: str, metadata: dict | None = None) -> dict:
        """
        Add a conversation turn to memory.

        Args:
            user_input: The user's message
            agent_response: The agent's response
            metadata: Optional metadata for this turn

        Returns:
            The created turn object
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
        self.updated_at = turn["timestamp"]

        # Auto-save after each turn
        self.save()

        return turn

    def get_recent_context(self, n_turns: int = 5) -> list[dict]:
        """
        Get the most recent n turns from history.

        Args:
            n_turns: Number of recent turns to retrieve

        Returns:
            List of recent conversation turns
        """
        # Convert deque to list and get last n items
        history_list = list(self.history)
        return history_list[-n_turns:] if history_list else []

    def build_llm_context(self, current_query: str, include_summaries: bool = True, max_turns: int = 5) -> str:
        """
        Build context string for LLM prompt engineering.

        Args:
            current_query: The current user query
            include_summaries: Whether to include conversation summaries
            max_turns: Maximum number of recent turns to include

        Returns:
            Formatted context string for LLM
        """
        context_parts = []

        # Add conversation metadata if relevant
        if self.metadata.get("total_turns", 0) > self.max_turns:
            context_parts.append(f"[Conversation info: Total {self.metadata['total_turns']} turns, showing recent {max_turns} turns]")

        # Add summaries if available and requested
        if include_summaries and self.summaries:
            context_parts.append("Previous conversation summary:")
            for summary in self.summaries[-3:]:  # Include last 3 summaries max
                context_parts.append(f"- {summary['content']}")
            context_parts.append("")  # Empty line for separation

        # Add recent conversation history
        recent_turns = self.get_recent_context(max_turns)
        if recent_turns:
            context_parts.append("Recent conversation:")
            for turn in recent_turns:
                # Format timestamp for readability
                timestamp = turn["timestamp"].split("T")[0]  # Just the date
                context_parts.append(f"[{timestamp}] User: {turn['user_input']}")
                context_parts.append(f"[{timestamp}] Assistant: {turn['agent_response']}")
                context_parts.append("")  # Empty line between turns

        # Add current query
        context_parts.append(f"Current user query: {current_query}")

        return "\n".join(context_parts)

    def search_history(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Simple keyword search through conversation history.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of matching conversation turns
        """
        query_lower = query.lower()
        matches = []

        for turn in self.history:
            if query_lower in turn["user_input"].lower() or query_lower in turn["agent_response"].lower():
                matches.append(turn)
                if len(matches) >= max_results:
                    break

        return matches

    def create_summary(self, start_idx: int | None = None, end_idx: int | None = None) -> dict:
        """
        Create a summary of conversation segment (placeholder for Phase 2).

        Args:
            start_idx: Starting index in history
            end_idx: Ending index in history

        Returns:
            Summary object
        """
        # For now, create a simple summary
        # In Phase 2, this will use LLM or rule-based summarization
        history_list = list(self.history)
        segment = history_list[start_idx:end_idx]

        if not segment:
            return {}

        summary = {
            "summary_id": str(uuid.uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "turn_count": len(segment),
            "content": f"Conversation segment with {len(segment)} turns",
            "start_timestamp": segment[0]["timestamp"],
            "end_timestamp": segment[-1]["timestamp"],
        }

        self.summaries.append(summary)
        return summary

    def save(self, backup: bool = True) -> None:
        """
        Save conversation memory to JSON file.

        Args:
            backup: Whether to create a backup before saving
        """
        # Create backup if requested and file exists
        if backup and self.filepath.exists():
            backup_path = self.filepath.with_suffix(".json.bak")
            shutil.copy2(self.filepath, backup_path)

        # Prepare data for serialization
        data = {
            "conversation_id": self.conversation_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "history": list(self.history),  # Convert deque to list
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

    def load(self) -> bool:
        """
        Load conversation memory from JSON file.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.filepath.exists():
            return False

        try:
            with open(self.filepath) as f:
                data = json.load(f)

            # Restore conversation data
            self.conversation_id = data.get("conversation_id", self.conversation_id)
            self.created_at = data.get("created_at", self.created_at)
            self.updated_at = data.get("updated_at", self.updated_at)
            self.summaries = data.get("summaries", [])
            self.metadata = data.get("metadata", self.metadata)

            # Restore history into deque
            history_data = data.get("history", [])
            self.history.clear()
            for turn in history_data:
                self.history.append(turn)

            # Update session count
            self.metadata["session_count"] = self.metadata.get("session_count", 0) + 1

            return True

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading conversation memory: {e}")
            # Try to load backup if available
            backup_path = self.filepath.with_suffix(".json.bak")
            if backup_path.exists():
                shutil.copy2(backup_path, self.filepath)
                return self.load()  # Recursive call to load backup
            return False

    def clear(self) -> None:
        """Clear all conversation history and reset metadata."""
        self.history.clear()
        self.summaries.clear()
        self.conversation_id = str(uuid.uuid4())
        self.created_at = datetime.now(UTC).isoformat()
        self.updated_at = self.created_at
        self.metadata = {"session_count": 1, "total_turns": 0}
        self.save()

    def get_statistics(self) -> dict[str, Any]:
        """
        Get conversation statistics.

        Returns:
            Dictionary with conversation statistics
        """
        history_list = list(self.history)

        return {
            "conversation_id": self.conversation_id,
            "total_turns": self.metadata.get("total_turns", 0),
            "total_messages": self.metadata.get("total_turns", 0),  # Alias for backward compatibility
            "active_turns": len(history_list),
            "summary_count": len(self.summaries),
            "session_count": self.metadata.get("session_count", 1),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "oldest_turn": history_list[0]["timestamp"] if history_list else None,
            "newest_turn": history_list[-1]["timestamp"] if history_list else None,
        }

    def __repr__(self) -> str:
        """String representation of ConversationMemory."""
        stats = self.get_statistics()
        return (
            f"ConversationMemory(id={stats['conversation_id'][:8]}..., "
            f"turns={stats['active_turns']}/{stats['total_turns']}, "
            f"summaries={stats['summary_count']})"
        )
