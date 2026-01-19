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
    TIMELINE_SUMMARY = "timeline_summary"  # Compressed history summary
    CONTEXT = "context"  # Ephemeral runtime context (time, user, location)
    TODO_LIST = "todo_list"  # Agent's task tracking list


# Static mapping of entry types to display labels
# Using concise labels to avoid model mimicking patterns like "[Agent's Internal Thoughts]"
ENTRY_CONFIG: Final = {
    TimelineEntryType.USER_MESSAGE: "USER",
    TimelineEntryType.AGENT_RESPONSE: "RESPONSE",
    TimelineEntryType.AGENT_THOUGHTS: "THOUGHT",
    TimelineEntryType.AGENT_LEARNING: "LEARNING",
    TimelineEntryType.SUB_AGENT_RESPONSE: "SUBAGENT",
    TimelineEntryType.RESOURCE_RESULT: "TOOL_RESULT",
    TimelineEntryType.WORKFLOW_RESULT: "WORKFLOW_RESULT",
    TimelineEntryType.UNKNOWN_TOOL_CALL: "UNKNOWN_TOOL",
    TimelineEntryType.TOOL_CALL: "TOOL_CALL",
    TimelineEntryType.TIMELINE_SUMMARY: "SUMMARY",
    TimelineEntryType.CONTEXT: "CONTEXT",
    TimelineEntryType.TODO_LIST: "TODO",
}


@dataclass
class TimelineConfig:
    """Configuration for timeline compression and management."""

    max_context_tokens: int = 4000
    compression_threshold: float = 0.8  # Trigger compression at 80% of max tokens
    compression_enabled: bool = True
    min_entries_before_compress: int = 5  # Don't compress until we have at least this many entries
    keep_recent_entries: int = 3  # Number of recent entries to preserve during compression


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
        tool_call_id: For tool results, the ID linking back to the original tool call (OpenAI native tools)
        tool_calls: For assistant messages, the native tool calls array (OpenAI native tools)
        ephemeral: If True, entry is not persisted and only exists for current query
    """

    entry_type: TimelineEntryType
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now())
    metadata: dict = field(default_factory=dict)
    is_latest_user_message: bool = False
    tool_call_id: str | None = None  # For linking tool results to their calls
    tool_calls: list | None = None  # For assistant messages with native tool calls
    ephemeral: bool = False  # Ephemeral entries are not persisted

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
        config: TimelineConfig | None = None,
    ):
        """
        Initialize the Timeline.

        Args:
            max_context_tokens: Maximum number of tokens to include in context
            agent: Agent instance (can be None, for backward compatibility)
            repository_factory: Repository factory to create the repository
            config: Optional TimelineConfig for compression settings
        """
        self._config = config or TimelineConfig(max_context_tokens=max_context_tokens)
        self.max_context_tokens = self._config.max_context_tokens
        self._agent = agent
        self.timeline: list[TimelineEntry] = []

        # Create repository via factory (only if agent is provided)
        if agent is not None:
            self._repository = repository_factory.create(RepositoryType.TIMELINE, agent=agent)
        else:
            self._repository = None

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

    def set_context(self, context: dict[str, Any]) -> None:
        """
        Set or replace the ephemeral runtime context entry.

        This removes any existing CONTEXT entry and adds a fresh one.
        The context entry is ephemeral (not persisted) and provides
        runtime information like current time, user, and timezone.

        Args:
            context: Dictionary with context info (e.g., timestamp, user, timezone)
        """
        # Remove any existing CONTEXT entries
        self.timeline = [e for e in self.timeline if e.entry_type != TimelineEntryType.CONTEXT]

        # Format context for display
        context_parts = []
        if "timestamp" in context:
            context_parts.append(f"Current time: {context['timestamp']}")
        if "timezone" in context:
            context_parts.append(f"Timezone: {context['timezone']}")
        if "location" in context:
            context_parts.append(f"Location: {context['location']}")
        if "user" in context:
            context_parts.append(f"User: {context['user']}")

        content = " | ".join(context_parts) if context_parts else str(context)

        # Insert at the beginning of the timeline
        context_entry = TimelineEntry(
            entry_type=TimelineEntryType.CONTEXT,
            content=content,
            metadata=context,
            ephemeral=True,
        )
        self.timeline.insert(0, context_entry)

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
                    content = self._format_entry_content(entry)

                    # Handle native tool results (OpenAI format)
                    if entry.tool_call_id:
                        context_messages.append(LLMMessage(
                            role="tool",
                            content=content,
                            tool_call_id=entry.tool_call_id
                        ))
                    # Handle assistant messages with native tool calls
                    elif entry.tool_calls:
                        context_messages.append(LLMMessage(
                            role="assistant",
                            content=content,
                            tool_calls=entry.tool_calls
                        ))
                    else:
                        role = self._get_entry_role(entry, default_role)
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
            content = self._format_entry_content(entry)

            # Handle native tool results (OpenAI format)
            if entry.tool_call_id:
                messages.append(LLMMessage(
                    role="tool",
                    content=content,
                    tool_call_id=entry.tool_call_id
                ))
            # Handle assistant messages with native tool calls
            elif entry.tool_calls:
                messages.append(LLMMessage(
                    role="assistant",
                    content=content,
                    tool_calls=entry.tool_calls
                ))
            else:
                role = self._get_entry_role(entry, default_role)
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
        elif entry.entry_type == TimelineEntryType.CONTEXT:
            return "system"
        elif entry.entry_type in [
            TimelineEntryType.AGENT_RESPONSE,
            TimelineEntryType.AGENT_THOUGHTS,
            TimelineEntryType.AGENT_LEARNING,
            TimelineEntryType.SUB_AGENT_RESPONSE,
            TimelineEntryType.RESOURCE_RESULT,
            TimelineEntryType.WORKFLOW_RESULT,
            TimelineEntryType.UNKNOWN_TOOL_CALL,
            TimelineEntryType.TOOL_CALL,  # Agent's tool calls are assistant actions
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
        content = entry.content

        # Truncate large resource/workflow results to prevent context overflow
        # Large results (like 50KB weather JSON) overwhelm the LLM
        MAX_RESULT_CHARS = 4000
        if entry.entry_type in [TimelineEntryType.RESOURCE_RESULT, TimelineEntryType.WORKFLOW_RESULT]:
            content_str = str(content)
            if len(content_str) > MAX_RESULT_CHARS:
                content = content_str[:MAX_RESULT_CHARS] + f"\n... [truncated, total {len(content_str)} chars]"

        if entry.entry_type in [TimelineEntryType.USER_MESSAGE, TimelineEntryType.AGENT_RESPONSE]:
            return str(content)
        else:
            label = entry._get_display_label()
            return f"[{label}] {content}"

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

        Ephemeral entries (like CONTEXT) are excluded from persistence.

        Args:
            session_id: Session identifier
        """
        if self._repository is None:
            raise ValueError("Cannot save timeline: repository is None. Initialize Timeline with repository or agent.")

        # Filter out ephemeral entries before saving
        persistent_entries = [e for e in self.timeline if not e.ephemeral]
        self._repository.save(session_id, persistent_entries)
        logger.info(f"Saved timeline with {len(persistent_entries)} entries for session {session_id} (excluded {len(self.timeline) - len(persistent_entries)} ephemeral)")

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

    # ============================================================================
    # COMPRESSION METHODS
    # ============================================================================

    def needs_compression(self) -> bool:
        """
        Check if timeline compression is needed based on current token usage.

        Returns:
            True if compression should be triggered
        """
        if not self._config.compression_enabled:
            return False

        if len(self.timeline) < self._config.min_entries_before_compress:
            return False

        # Estimate current token usage
        messages = self.to_llm_messages()
        current_tokens = self._estimate_tokens(messages)
        threshold = self._config.max_context_tokens * self._config.compression_threshold

        return current_tokens > threshold

    def _estimate_entries_tokens(self, entries: list[TimelineEntry]) -> int:
        """
        Estimate token count for timeline entries.

        Args:
            entries: List of TimelineEntry objects

        Returns:
            Estimated token count
        """
        total = 0
        for entry in entries:
            # Rough estimation: 1.3 tokens per word
            total += len(entry.content.split()) * 1.3
        return int(total)

    def compress_old_entries(self, summary: str) -> int:
        """
        Compress old timeline entries into a summary entry.

        This method replaces old entries with a single TIMELINE_SUMMARY entry,
        preserving recent entries as configured.

        Args:
            summary: The summary text to use for the compressed entries

        Returns:
            Number of entries that were compressed
        """
        keep_recent = self._config.keep_recent_entries

        if len(self.timeline) <= keep_recent:
            return 0  # Nothing to compress

        # Get entries to compress (all except recent N)
        old_entries = self.timeline[:-keep_recent]
        recent_entries = self.timeline[-keep_recent:]

        if not old_entries:
            return 0

        # Create summary entry
        summary_entry = TimelineEntry(
            entry_type=TimelineEntryType.TIMELINE_SUMMARY,
            content=f"[Previous context summary] {summary}",
            timestamp=old_entries[0].timestamp,
        )

        # Replace timeline with summary + recent entries
        compressed_count = len(old_entries)
        self.timeline = [summary_entry] + recent_entries

        logger.info(
            f"Compressed {compressed_count} timeline entries into summary",
            compressed_count=compressed_count,
            remaining_entries=len(self.timeline),
        )

        return compressed_count

    def get_entries_for_compression(self) -> list[TimelineEntry]:
        """
        Get the entries that would be compressed (for generating a summary).

        Returns:
            List of old entries that would be replaced by a summary
        """
        keep_recent = self._config.keep_recent_entries

        if len(self.timeline) <= keep_recent:
            return []

        return self.timeline[:-keep_recent]

    def build_compression_prompt(self) -> str | None:
        """
        Build a prompt for LLM-based compression of old entries.

        Returns:
            Prompt string for summarization, or None if compression not needed
        """
        entries_to_compress = self.get_entries_for_compression()

        if not entries_to_compress:
            return None

        # Build entries text with truncation for very long entries
        # Use simple role labels to avoid model mimicking patterns like [thought] or [tool_call]
        role_map = {
            "user_message": "User",
            "agent_response": "Assistant",
            "thought": "Assistant thinking",
            "tool_call": "Tool called",
            "resource_result": "Tool result",
            "workflow_result": "Workflow result",
        }
        entries_text_parts = []
        for entry in entries_to_compress:
            content = entry.content[:500] + "..." if len(entry.content) > 500 else entry.content
            role = role_map.get(entry.entry_type.value, entry.entry_type.value)
            entries_text_parts.append(f"{role}: {content}")

        entries_text = "\n".join(entries_text_parts)

        return f"""Summarize this conversation history in 2-3 sentences,
preserving key facts, decisions, tool calls and their results.

Respond with a JSON object containing a "summary" field:
{{"summary": "your summary here"}}

Conversation history:
{entries_text}"""
