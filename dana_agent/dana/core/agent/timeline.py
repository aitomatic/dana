"""
Timeline system for agent conversation management.

This module provides a unified, chronological record of all agent interactions
with efficient context management to prevent context window explosion.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Final

from structlog import get_logger

from dana.common.llm.types import LLMMessage
from dana.repositories.repository_factory import DEFAULT_REPOSITORY_FACTORY, RepositoryFactory, RepositoryType


if TYPE_CHECKING:
    from dana.core.agent.base_agent import BaseAgent

logger = get_logger()


class TimelineEntryType(Enum):
    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"
    AGENT_THOUGHTS = "agent_thoughts"
    TOOL_CALL = "tool_call"
    FAILED_TOOL_CALL = "failed_tool_call"
    SUB_AGENT_RESPONSE = "sub_agent_response"
    RESOURCE_RESULT = "resource_result"
    WORKFLOW_RESULT = "workflow_result"
    UNKNOWN_TOOL_CALL = "unknown_tool_call"
    AGENT_LEARNING = "agent_learning"


# Static mapping of entry types to display labels
ENTRY_CONFIG: Final = {
    TimelineEntryType.USER_MESSAGE: "User-to-Agent Message",
    TimelineEntryType.AGENT_RESPONSE: "Agent-to-User Response",
    TimelineEntryType.AGENT_THOUGHTS: "Agent's Internal Thoughts",
    TimelineEntryType.AGENT_LEARNING: "Agent's Self-Learning",
    TimelineEntryType.SUB_AGENT_RESPONSE: "SubAgent-to-Agent Response",
    TimelineEntryType.RESOURCE_RESULT: "Resource-to-Agent Result",
    TimelineEntryType.WORKFLOW_RESULT: "Workflow-to-Agent Result",
    TimelineEntryType.UNKNOWN_TOOL_CALL: "Unknown Tool-to-Agent Result",
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

    def _get_entry_config(self) -> str:
        """
        Get the label for this entry type.

        Returns:
            Display label string
        """
        return ENTRY_CONFIG.get(self.entry_type, str(self.entry_type))

    def _get_display_label(self) -> str:
        """
        Get the display label for this entry type.

        Returns:
            Display label string
        """
        return self._get_entry_config()

    def _get_formatted_content(self) -> str:
        """
        Get formatted content with semantic labels.

        Returns:
            Formatted content string
        """
        if self.entry_type in [TimelineEntryType.USER_MESSAGE, TimelineEntryType.AGENT_RESPONSE]:
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
        return self.entry_type == TimelineEntryType.USER_MESSAGE

    def is_resource_result(self) -> bool:
        """
        Check if this is a resource result.

        Returns:
            True if this is a resource result
        """
        return self.entry_type == TimelineEntryType.RESOURCE_RESULT


def _sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize objects to make them JSON serializable.

    Converts non-serializable objects (like ReadFileResource) to serializable representations.

    Args:
        obj: Object to sanitize

    Returns:
        JSON-serializable representation of the object
    """
    if obj is None:
        return None
    elif isinstance(obj, str | int | float | bool):
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: _sanitize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list | tuple):
        return [_sanitize_for_json(item) for item in obj]
    elif isinstance(obj, Enum):
        return obj.value
    elif hasattr(obj, "__dict__"):
        # For objects with __dict__, convert to a dict representation
        # Include class name and object id if available
        result = {
            "__class__": obj.__class__.__name__,
            "__module__": getattr(obj.__class__, "__module__", "unknown"),
        }
        # Try to get object_id if it exists
        if hasattr(obj, "object_id"):
            result["object_id"] = obj.object_id
        # Try to get a string representation
        try:
            result["__repr__"] = repr(obj)
        except Exception:
            result["__repr__"] = f"<{obj.__class__.__name__} object>"
        return result
    else:
        # Fallback: convert to string representation
        try:
            return str(obj)
        except Exception:
            return f"<{type(obj).__name__} object>"


class Timeline:
    """
    Manages the timeline for an agent, handling context building and token management.

    The Timeline provides a unified, chronological record of all agent interactions
    with efficient context management to prevent context window explosion.
    """

    def __init__(
        self,
        max_context_tokens: int = 4000,
        agent: "BaseAgent | None" = None,
        repository_factory: RepositoryFactory = DEFAULT_REPOSITORY_FACTORY,
    ):
        """
        Initialize the Timeline.

        Args:
            max_context_tokens: Maximum number of tokens to include in context
            agent: Agent instance (can be None, for backward compatibility)
            codec: Codec class for path structure (can be None, for backward compatibility)
            repository_factory: Repository factory to create the repository
        """
        self.max_context_tokens = max_context_tokens
        self._agent = agent
        self.timeline: list[TimelineEntry] = []

        # Create repository via factory
        self._repository = repository_factory.create(RepositoryType.TIMELINE, agent=agent)

    def __repr__(self) -> str:
        """
        Return a string representation of the timeline.

        Returns:
            String representation of the timeline
        """
        return f"Timeline(max_context_tokens={self.max_context_tokens}, timeline={self.timeline[-10:]})"

    def add_entry(self, entry: TimelineEntry) -> None:
        """
        Add entry to timeline.

        Args:
            entry: TimelineEntry to add
        """
        self.timeline.append(entry)

    def to_llm_messages(
        self, max_tokens: int | None = None, default_role: str = "user", separate_latest_user: bool = False
    ) -> list[LLMMessage]:
        """
        Convert timeline entries to LLM messages with proper role assignment and token management.

        This method encapsulates the logic for:
        - Role assignment based on entry type
        - Sliding window for recent entries
        - Token-based compaction
        - Chronological ordering
        - Optional separation of latest user message

        Args:
            max_tokens: Maximum tokens to include (overrides max_context_tokens)
            default_role: Default role for entries that don't have a specific role mapping
            separate_latest_user: If True, separates latest user message from context

        Returns:
            List of LLMMessage objects in chronological order
        """
        token_limit = max_tokens or self.max_context_tokens

        if separate_latest_user:
            # Find latest user message
            latest_user_entry = next((entry for entry in self.timeline if entry.is_latest_user_message), None)

            if latest_user_entry:
                # Get context entries (excluding latest user message)
                context_entries = [entry for entry in self.timeline if not entry.is_latest_user_message]

                # Convert context entries to messages
                context_messages = []
                for entry in context_entries:
                    role = self._get_entry_role(entry, default_role)
                    content = self._format_entry_content(entry)
                    context_messages.append(LLMMessage(role=role, content=content))

                # Apply token limit to context if needed
                if self._estimate_tokens(context_messages) > token_limit:
                    context_messages = self._build_context_with_token_limit(context_messages, token_limit)

                # Add latest user message as separate message
                latest_user_message = LLMMessage(role="user", content=latest_user_entry.content)
                context_messages.append(latest_user_message)

                # Mark latest user message as processed
                latest_user_entry.is_latest_user_message = False

                return context_messages

        # Standard processing (no latest user separation)
        timeline_entries = self.timeline

        # Convert entries to LLM messages
        messages = []
        for entry in timeline_entries:
            role = self._get_entry_role(entry, default_role)
            content = self._format_entry_content(entry)
            messages.append(LLMMessage(role=role, content=content))

        # Apply token limit if needed
        if self._estimate_tokens(messages) > token_limit:
            return self._build_context_with_token_limit(messages, token_limit)

        return messages

    def _get_entry_role(self, entry: TimelineEntry, default_role: str) -> str:
        """
        Get the LLM role for a timeline entry.

        Args:
            entry: TimelineEntry to get role for
            default_role: Default role if no specific mapping exists

        Returns:
            LLM role string (user, assistant, system)
        """
        if entry.entry_type == TimelineEntryType.USER_MESSAGE:
            return "user"
        elif entry.entry_type in [
            TimelineEntryType.AGENT_RESPONSE,
            TimelineEntryType.AGENT_THOUGHTS,
            TimelineEntryType.AGENT_LEARNING,
            TimelineEntryType.SUB_AGENT_RESPONSE,
            TimelineEntryType.RESOURCE_RESULT,
            TimelineEntryType.WORKFLOW_RESULT,
            TimelineEntryType.UNKNOWN_TOOL_CALL,
        ]:
            return "assistant"
        else:
            return default_role

    def _format_entry_content(self, entry: TimelineEntry) -> str:
        """
        Format timeline entry content for LLM consumption.

        Args:
            entry: TimelineEntry to format

        Returns:
            Formatted content string
        """
        if entry.entry_type in [TimelineEntryType.USER_MESSAGE, TimelineEntryType.AGENT_RESPONSE]:
            return entry.content
        else:
            label = entry._get_display_label()
            return f"[{label}] {entry.content}"

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

    def _build_context_with_token_limit(self, messages: list[LLMMessage], max_tokens: int) -> list[LLMMessage]:
        """
        Build context using token limit approach with sliding window.

        Args:
            messages: All messages in chronological order
            max_tokens: Maximum tokens to include

        Returns:
            List of LLMMessage objects within token limit
        """
        # Start with most recent messages and work backwards
        result = []
        current_tokens = 0

        for message in reversed(messages):
            message_tokens = self._estimate_tokens([message])

            if current_tokens + message_tokens > max_tokens:
                break

            result.insert(0, message)  # Insert at beginning to maintain chronological order
            current_tokens += message_tokens

        return result

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

    def save(self, session_id: str) -> None:
        """
        Save timeline for a session.

        Args:
            session_id: Session identifier
        """
        if self._repository is None:
            raise ValueError("Cannot save timeline: repository is None. Initialize Timeline with repository or agent.")

        self._repository.save(session_id, self.timeline)
        logger.info(f"Saved timeline with {len(self.timeline)} entries for session {session_id}")

    def read_since(self, checkpoint: int) -> Iterator[TimelineEntry]:
        """
        Read timeline entries since checkpoint for the current session.

        Args:
            checkpoint: Starting index for reading entries.
                Negative values are supported (e.g., -10 means "last 10 entries").
                -1 means "last entry only", -2 means "last 2 entries", etc.

        Yields:
            TimelineEntry objects since checkpoint
        """
        if self._repository is None:
            raise ValueError("Cannot read timeline: repository is None. Initialize Timeline with repository or agent.")

        if self._agent is None:
            raise ValueError("Cannot read timeline: agent is None. Session ID cannot be extracted.")

        # Extract session_id from agent
        session_id = getattr(self._agent, "_session_id", None)
        if session_id is None:
            raise ValueError("Cannot read timeline: agent has no _session_id. Set session_id on agent first.")

        # Collect all entries from the session
        all_entries = list(self._repository.read_session_entries(session_id))

        # Convert negative checkpoint to positive index
        if checkpoint < 0:
            total_count = len(all_entries)
            # Convert negative index: -1 = last entry, -2 = second to last, etc.
            # Similar to Python list slicing: checkpoint = total_count + checkpoint
            checkpoint = max(0, total_count + checkpoint)

        # Yield entries from checkpoint onwards
        for i in range(checkpoint, len(all_entries)):
            yield all_entries[i]
