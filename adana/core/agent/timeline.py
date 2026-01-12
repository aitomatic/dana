"""
Timeline system for agent conversation management.

This module provides a unified, chronological record of all agent interactions
with efficient context management to prevent context window explosion.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Final

from adana.common.llm.types import LLMMessage


class TimelineEntryType(Enum):
    CALLER_MESSAGE = "caller_message"
    MY_RESPONSE = "my_response"
    MY_THOUGHTS = "my_thoughts"
    TOOL_CALL = "tool_call"
    AGENT_RESPONSE = "agent_response"
    RESOURCE_RESULT = "resource_result"
    WORKFLOW_RESULT = "workflow_result"
    UNKNOWN_TOOL_CALL = "unknown_tool_call"
    MY_LEARNING = "my_learning"


# Static mapping of entry types to (role, label) tuples
ENTRY_CONFIG: Final = {
    TimelineEntryType.CALLER_MESSAGE: ("user", "User/Caller Message"),
    TimelineEntryType.MY_RESPONSE: ("assistant", "My Response"),
    TimelineEntryType.MY_THOUGHTS: ("system", "My Thoughts"),
    TimelineEntryType.MY_LEARNING: ("system", "My Learning"),
    TimelineEntryType.AGENT_RESPONSE: ("system", "Tool Response (Agent)"),
    TimelineEntryType.RESOURCE_RESULT: ("system", "Tool Response (Resource)"),
    TimelineEntryType.WORKFLOW_RESULT: ("system", "Tool Response (Workflow)"),
    TimelineEntryType.UNKNOWN_TOOL_CALL: ("system", "Tool Response (Unknown)"),
    TimelineEntryType.TOOL_CALL: ("system", "Tool Call"),
}


@dataclass
class TimelineEntry:
    """
    A single entry in an agent's timeline representing one interaction or event.

    Attributes:
        timestamp: When the interaction occurred
        entry_type: Type of interaction (CALLER_MESSAGE, MY_RESPONSE, etc.)
        content: The actual content/message
        metadata: Additional context information
        is_latest_user_message: Whether this is the latest user message
    """

    entry_type: TimelineEntryType
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now())
    metadata: dict = field(default_factory=dict)
    is_latest_user_message: bool = False

    def _get_entry_config(self) -> tuple[str, str]:
        """
        Get the role and label for this entry type.

        Returns:
            Tuple of (role, label)
        """
        return ENTRY_CONFIG.get(self.entry_type, ("user", str(self.entry_type)))

    def _get_llm_role(self) -> str:
        """
        Get the LLM role for this entry type.

        Returns:
            LLM role string (user, assistant, system)
        """
        role, _ = self._get_entry_config()
        return role

    def _get_display_label(self) -> str:
        """
        Get the display label for this entry type.

        Returns:
            Display label string
        """
        _, label = self._get_entry_config()
        return label

    def _get_formatted_content(self) -> str:
        """
        Get formatted content with semantic labels.

        Returns:
            Formatted content string
        """
        if self.entry_type in [TimelineEntryType.CALLER_MESSAGE, TimelineEntryType.MY_RESPONSE]:
            return self.content
        else:
            label = self._get_display_label()
            return f"[{label}] {self.content}"

    def _format_content_for_llm(self) -> str:
        """
        Format content for LLM consumption.

        Returns:
            Formatted content string with semantic context
        """
        return self._get_formatted_content()

    def to_llm_message(self) -> LLMMessage:
        """
        Convert to LLM message format for context building.

        Returns:
            LLMMessage object suitable for LLM context
        """
        role = self._get_llm_role()
        content = self._format_content_for_llm()
        return LLMMessage(role=role, content=content)

    def _get_display_content(self) -> str:
        """
        Get the display content for this entry.

        Returns:
            Display content string
        """
        return self.content

    def to_string(self) -> str:
        """
        Convert to human-readable string format.

        Returns:
            Human-readable string representation
        """
        timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        label = self._get_display_label()
        content = self._get_display_content()
        return f"[{timestamp_str}] [{label}] {content}"

    def is_caller_message(self) -> bool:
        """
        Check if this is a caller message (from user or agent).

        Returns:
            True if this is a caller message
        """
        return self.entry_type == TimelineEntryType.CALLER_MESSAGE

    def is_resource_result(self) -> bool:
        """
        Check if this is a resource result.

        Returns:
            True if this is a resource result
        """
        return self.entry_type == TimelineEntryType.RESOURCE_RESULT


class Timeline:
    """
    Manages the timeline for an agent, handling context building and token management.

    The Timeline provides a unified, chronological record of all agent interactions
    with efficient context management to prevent context window explosion.
    """

    def __init__(self, max_context_tokens: int = 4000):
        """
        Initialize the Timeline.

        Args:
            max_context_tokens: Maximum number of tokens to include in context
        """
        self.timeline: list[TimelineEntry] = []
        self.max_context_tokens = max_context_tokens

    def add_entry(self, entry: TimelineEntry) -> None:
        """
        Add entry to timeline.

        Args:
            entry: TimelineEntry to add
        """
        self.timeline.append(entry)

    def get_context(self, max_tokens: int | None = None) -> list[LLMMessage]:
        """
        Get timeline context within token limits.

        Args:
            max_tokens: Maximum tokens to include (overrides max_context_tokens)

        Returns:
            List of LLMMessage objects for LLM context
        """
        token_limit = max_tokens or self.max_context_tokens
        return self._build_context_with_token_limit(token_limit)

    def to_llm_messages(self, max_tokens: int | None = None) -> list[LLMMessage]:
        """
        Get timeline context optimized for LLM processing with strict chronological ordering.

        This method maintains true chronological order of all timeline entries,
        which is crucial for multi-agent coordination and conversation flow.

        Args:
            max_tokens: Maximum tokens to include (overrides max_context_tokens)

        Returns:
            List of LLMMessage objects in strict chronological order
        """
        token_limit = max_tokens or self.max_context_tokens

        # Get all timeline entries in chronological order
        timeline_entries = self.timeline

        # Convert all entries to LLM messages in chronological order
        # This maintains the true temporal sequence of events
        messages = []
        for entry in timeline_entries:
            messages.append(entry.to_llm_message())

        # Apply token limit if needed
        if self._estimate_tokens(messages) > token_limit:
            return self._build_context_with_token_limit(token_limit)

        return messages

    def get_recent_entries(self, count: int) -> list[TimelineEntry]:
        """
        Get most recent N entries.

        Args:
            count: Number of recent entries to return

        Returns:
            List of most recent TimelineEntry objects
        """
        return self.timeline[-count:] if count > 0 else []

    def get_entries_by_type(self, entry_type: str) -> list[TimelineEntry]:
        """
        Get entries filtered by type.

        Args:
            entry_type: Type of entries to filter by

        Returns:
            List of TimelineEntry objects of specified type
        """
        return [entry for entry in self.timeline if entry.entry_type == entry_type]

    def clear_old_entries(self, before_timestamp: datetime) -> int:
        """
        Remove entries before timestamp.

        Args:
            before_timestamp: Remove entries before this timestamp

        Returns:
            Number of entries removed
        """
        original_count = len(self.timeline)
        self.timeline = [entry for entry in self.timeline if entry.timestamp >= before_timestamp]

        return original_count - len(self.timeline)

    def _estimate_tokens(self, messages: list[LLMMessage]) -> int:
        """
        Estimate token count for messages.

        Args:
            messages: List of LLMMessage objects

        Returns:
            Estimated token count
        """
        total = 0
        for msg in messages:
            # Rough estimation: 1.3 tokens per word
            total += len(msg.content.split()) * 1.3
        return int(total)

    def _build_context_with_sliding_window(self, window_size: int) -> list[LLMMessage]:
        """
        Build context using sliding window approach.

        Args:
            window_size: Number of recent entries to include

        Returns:
            List of LLMMessage objects for context
        """
        recent_entries = self.get_recent_entries(window_size)
        return [entry.to_llm_message() for entry in recent_entries]

    def _build_context_with_token_limit(self, max_tokens: int) -> list[LLMMessage]:
        """
        Build context using token limit approach.

        Args:
            max_tokens: Maximum tokens to include

        Returns:
            List of LLMMessage objects for context
        """
        messages = []

        # Add entries from most recent to oldest
        for entry in reversed(self.timeline):
            entry_message = entry.to_llm_message()
            messages.insert(0, entry_message)

            # Check if we're approaching token limit
            if self._estimate_tokens(messages) > max_tokens:
                # Remove oldest message to stay within limits
                messages.pop(0)
                break

        return messages

    def get_timeline_summary(self) -> str:
        """
        Get a summary of the timeline.

        Returns:
            Human-readable timeline summary
        """
        if not self.timeline:
            return "Timeline is empty"

        summary_lines = []
        for entry in self.timeline:
            summary_lines.append(entry.to_string())

        return "\n".join(summary_lines)

    def get_entry_count(self) -> int:
        """
        Get total number of entries in timeline.

        Returns:
            Number of entries
        """
        return len(self.timeline)

    def get_entry_count_by_type(self) -> dict[str, int]:
        """
        Get count of entries by type.

        Returns:
            Dictionary mapping entry types to counts
        """
        counts = {}
        for entry in self.timeline:
            counts[entry.entry_type] = counts.get(entry.entry_type, 0) + 1
        return counts
