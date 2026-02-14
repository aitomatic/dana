"""
Compressed Timeline with intelligent context management.

This module provides a Timeline subclass that implements progressive compression
using LLM-based summarization, similar to Claude Code's compression technique.

Key features:
- Token-based compression triggers
- Stores compressed context in entry metadata for efficient loading
- Progressive compression that preserves recent context
- Native message format for provider-agnostic LLM integration
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from structlog import get_logger

from dana.common.llm.types import LLMMessage
from dana.core.agent.timeline import (
    Timeline,
    TimelineConfig,
    TimelineEntry,
    TimelineEntryType,
)
from dana.repositories.repository_factory import DEFAULT_REPOSITORY_FACTORY, RepositoryFactory


if TYPE_CHECKING:
    from dana.core.agent.base_agent import BaseAgent

logger = get_logger()


# Type alias for native message roles
NativeMessageRole = Literal["user", "assistant", "system", "tool"]


@dataclass
class NativeToolCall:
    """
    Represents a tool/function call made by the assistant.

    This is a provider-agnostic representation of tool calls that can be
    converted to provider-specific formats (OpenAI, Anthropic, etc.).

    Attributes:
        id: Unique identifier for this tool call (used to link with tool results)
        name: Name of the tool/function being called
        arguments: JSON-serializable arguments passed to the tool
    """

    id: str
    name: str
    arguments: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for JSON persistence."""
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NativeToolCall:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            arguments=data.get("arguments", {}),
        )


@dataclass
class NativeMessage:
    """
    Provider-agnostic message format for LLM conversations.

    This dataclass represents a single message in a conversation that can be
    converted to any LLM provider's format (OpenAI, Anthropic, etc.). It stores
    messages in a normalized structure that preserves all necessary information
    for tool calling workflows.

    Attributes:
        role: Message role - 'user', 'assistant', 'system', or 'tool'
        content: The text content of the message
        tool_calls: For assistant messages, list of tool invocations made
        tool_call_id: For tool messages, the ID linking this result to its call
        metadata: Additional provider-agnostic metadata
        timestamp: When this message was created

    Usage:
        # User message
        user_msg = NativeMessage(role="user", content="Hello!")

        # Assistant message with tool call
        assistant_msg = NativeMessage(
            role="assistant",
            content="Let me check that for you.",
            tool_calls=[NativeToolCall(id="call_123", name="search", arguments={"q": "test"})]
        )

        # Tool result
        tool_msg = NativeMessage(
            role="tool",
            content='{"results": [...]}',
            tool_call_id="call_123"
        )
    """

    role: NativeMessageRole
    content: str
    tool_calls: list[NativeToolCall] | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate message consistency after initialization."""
        # Validate role
        valid_roles = {"user", "assistant", "system", "tool"}
        if self.role not in valid_roles:
            raise ValueError(f"Invalid role '{self.role}'. Must be one of: {valid_roles}")

        # tool_calls should only be on assistant messages
        if self.tool_calls and self.role != "assistant":
            raise ValueError("tool_calls can only be set on assistant messages")

        # tool_call_id should only be on tool messages
        if self.tool_call_id and self.role != "tool":
            raise ValueError("tool_call_id can only be set on tool messages")

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize message to dictionary for JSON persistence.

        Returns:
            JSON-serializable dictionary representation
        """
        result: dict[str, Any] = {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.tool_calls:
            result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]

        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id

        if self.metadata:
            result["metadata"] = self.metadata

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NativeMessage:
        """
        Deserialize message from dictionary.

        Args:
            data: Dictionary representation of the message

        Returns:
            NativeMessage instance
        """
        tool_calls = None
        if "tool_calls" in data and data["tool_calls"]:
            tool_calls = [NativeToolCall.from_dict(tc) for tc in data["tool_calls"]]

        timestamp = datetime.now()
        if "timestamp" in data:
            timestamp = datetime.fromisoformat(data["timestamp"])

        return cls(
            role=data["role"],
            content=data.get("content", ""),
            tool_calls=tool_calls,
            tool_call_id=data.get("tool_call_id"),
            metadata=data.get("metadata", {}),
            timestamp=timestamp,
        )

    def to_llm_message(self) -> LLMMessage:
        """
        Convert to LLMMessage for use with existing LLM infrastructure.

        Returns:
            LLMMessage instance
        """
        # Convert NativeToolCall to the format expected by LLMMessage
        tool_calls_for_llm = None
        if self.tool_calls:
            tool_calls_for_llm = [tc.to_dict() for tc in self.tool_calls]

        return LLMMessage(
            role=self.role,
            content=self.content,
            tool_calls=tool_calls_for_llm,
            tool_call_id=self.tool_call_id,
        )


# Metadata keys for compressed context storage
COMPRESSED_CONTEXT_KEY = "compressed_context"
COMPRESSION_TIMESTAMP_KEY = "compression_timestamp"
COMPRESSED_ENTRIES_COUNT_KEY = "compressed_entries_count"


@dataclass
class CompressedTimelineConfig(TimelineConfig):
    """Configuration for compressed timeline with enhanced context management."""

    # Maximum tokens before compression is triggered
    max_tokens_until_compression: int = 80000

    # Maximum number of recent entries to keep uncompressed
    max_recent_entries_to_keep: int = 20

    # Token cutoff for recent entries (default 30% of max_tokens_until_compression)
    # Set to 0 or None to use the default calculation
    cutoff_when_token_reach: int | None = None

    def __post_init__(self) -> None:
        """Calculate default cutoff if not specified."""
        if self.cutoff_when_token_reach is None or self.cutoff_when_token_reach == 0:
            self.cutoff_when_token_reach = int(0.3 * self.max_tokens_until_compression)


class CompressedTimeline(Timeline):
    """
    Timeline with intelligent compression and context management.

    This Timeline subclass implements the TimelineProtocol interface and provides
    progressive compression using LLM-based summarization. It tracks token usage
    and compresses older entries when thresholds are reached, storing the compressed
    context in metadata for efficient session loading.

    Compression triggers when:
    - Total tokens exceed max_tokens_until_compression, OR
    - Number of entries exceeds a threshold

    Compression behavior:
    1. Iterate through entries from latest to oldest
    2. Count tokens until reaching cutoff_when_token_reach OR max_recent_entries_to_keep
    3. Compress all older entries using LLM summarization
    4. Store compressed context in metadata of the oldest kept entry
    5. Remove compressed entries from the timeline

    Loading optimization:
    - When loading entries, check for compressed context in metadata
    - If found, load the compressed context and skip older entries
    """

    def __init__(
        self,
        max_tokens_until_compression: int = 80000,
        max_recent_entries_to_keep: int = 20,
        cutoff_when_token_reach: int | None = None,
        agent: BaseAgent | None = None,
        repository_factory: RepositoryFactory = DEFAULT_REPOSITORY_FACTORY,
        llm_call_fn: Callable[[str], str] | None = None,
        llm_call_async_fn: Callable[[str], Any] | None = None,
    ):
        """
        Initialize the CompressedTimeline.

        Args:
            max_tokens_until_compression: Maximum tokens before compression triggers
            max_recent_entries_to_keep: Maximum number of recent entries to preserve
            cutoff_when_token_reach: Token cutoff for recent entries (default 30% of max)
            agent: Agent instance (can be None, for backward compatibility)
            repository_factory: Repository factory to create the repository
            llm_call_fn: Synchronous function to call LLM for compression
            llm_call_async_fn: Async function to call LLM for compression
        """
        # Calculate cutoff if not specified
        if cutoff_when_token_reach is None or cutoff_when_token_reach == 0:
            cutoff_when_token_reach = int(0.3 * max_tokens_until_compression)

        # Create config
        self._compressed_config = CompressedTimelineConfig(
            max_context_tokens=max_tokens_until_compression,
            max_tokens_until_compression=max_tokens_until_compression,
            max_recent_entries_to_keep=max_recent_entries_to_keep,
            cutoff_when_token_reach=cutoff_when_token_reach,
            compression_enabled=True,
        )

        # Initialize parent
        super().__init__(
            max_context_tokens=max_tokens_until_compression,
            agent=agent,
            repository_factory=repository_factory,
            config=self._compressed_config,
        )

        # Store LLM call functions for compression
        self._llm_call_fn = llm_call_fn
        self._llm_call_async_fn = llm_call_async_fn

        # Internal storage for native message format
        self._native_messages: list[NativeMessage] = []

    @property
    def max_tokens_until_compression(self) -> int:
        """Get max tokens threshold."""
        return self._compressed_config.max_tokens_until_compression

    @property
    def max_recent_entries_to_keep(self) -> int:
        """Get max recent entries to keep."""
        return self._compressed_config.max_recent_entries_to_keep

    @property
    def cutoff_when_token_reach(self) -> int:
        """Get token cutoff for recent entries."""
        return self._compressed_config.cutoff_when_token_reach or int(0.3 * self._compressed_config.max_tokens_until_compression)

    def set_llm_call_fn(self, fn: Callable[[str], str]) -> None:
        """Set the synchronous LLM call function."""
        self._llm_call_fn = fn

    def set_llm_call_async_fn(self, fn: Callable[[str], Any]) -> None:
        """Set the async LLM call function."""
        self._llm_call_async_fn = fn

    def add_entry(self, entry: TimelineEntry) -> None:
        """
        Add entry to timeline, converting to native message format.

        Overrides the parent add_entry() to convert TimelineEntry to NativeMessage
        before storing internally. The original entry is still added to self.timeline
        for backward compatibility.

        Mapping:
        - USER_MESSAGE -> role='user'
        - AGENT_RESPONSE -> role='assistant'
        - AGENT_THOUGHTS -> role='assistant'
        - TOOL_CALL -> role='assistant' with tool_calls
        - RESOURCE_RESULT -> role='tool'
        - WORKFLOW_RESULT -> role='tool'
        - TIMELINE_SUMMARY -> role='system'
        - CONTEXT -> role='system'
        - Other -> role='assistant' (default)

        Args:
            entry: TimelineEntry to add
        """
        # Add to parent timeline for backward compatibility
        super().add_entry(entry)

        # Convert to native message and store
        native_msg = self._timeline_entry_to_native_message(entry)
        self._native_messages.append(native_msg)

    def _timeline_entry_to_native_message(self, entry: TimelineEntry) -> NativeMessage:
        """
        Convert a TimelineEntry to NativeMessage format.

        Mapping rules:
        - USER_MESSAGE -> role='user'
        - AGENT_RESPONSE, AGENT_THOUGHTS, AGENT_LEARNING, SUB_AGENT_RESPONSE, TODO_LIST
          -> role='assistant'
        - TOOL_CALL -> role='assistant' with tool_calls
        - RESOURCE_RESULT, WORKFLOW_RESULT -> role='tool' with tool_call_id
        - TIMELINE_SUMMARY, CONTEXT -> role='system'
        - Other -> role='assistant' (default)

        Args:
            entry: TimelineEntry to convert

        Returns:
            NativeMessage in provider-agnostic format
        """
        role: NativeMessageRole
        tool_calls: list[NativeToolCall] | None = None
        tool_call_id: str | None = None

        # Map entry type to role
        if entry.entry_type == TimelineEntryType.USER_MESSAGE:
            role = "user"
        elif entry.entry_type in (
            TimelineEntryType.TIMELINE_SUMMARY,
            TimelineEntryType.CONTEXT,
        ):
            role = "system"
        elif entry.entry_type in (
            TimelineEntryType.RESOURCE_RESULT,
            TimelineEntryType.WORKFLOW_RESULT,
        ):
            role = "tool"
            tool_call_id = entry.tool_call_id
        elif entry.entry_type == TimelineEntryType.TOOL_CALL:
            role = "assistant"
            # Convert entry.tool_calls to NativeToolCall list
            if entry.tool_calls:
                tool_calls = []
                for tc in entry.tool_calls:
                    # Handle both dict and object formats
                    if isinstance(tc, dict):
                        # Support multiple formats:
                        # 1. Runtime format: {"function": "name", "arguments": {...}, "tool_call_id": "..."}
                        # 2. OpenAI nested: {"id": "...", "function": {"name": "...", "arguments": "..."}}
                        # 3. Direct format: {"id": "...", "name": "...", "arguments": {...}}
                        tc_id = tc.get("id", "") or tc.get("tool_call_id", "")

                        # Get function name - handle both string and nested dict formats
                        tc_function = tc.get("function")
                        if isinstance(tc_function, str):
                            # Runtime format: "function" is the name string
                            tc_name = tc_function
                        elif isinstance(tc_function, dict):
                            # OpenAI nested format: "function" is {"name": "...", "arguments": "..."}
                            tc_name = tc_function.get("name", "")
                        else:
                            # Direct format: "name" key exists
                            tc_name = tc.get("name", "")

                        # Get arguments - handle both direct and nested formats
                        tc_args = tc.get("arguments")
                        if tc_args is None and isinstance(tc_function, dict):
                            tc_args = tc_function.get("arguments", {})
                        # Handle string arguments (JSON string from OpenAI format)
                        if isinstance(tc_args, str):
                            import json

                            try:
                                tc_args = json.loads(tc_args)
                            except json.JSONDecodeError:
                                tc_args = {"raw": tc_args}
                        # Default to empty dict if still None
                        if tc_args is None:
                            tc_args = {}
                    else:
                        # Object with attributes
                        tc_id = getattr(tc, "id", "")
                        tc_name = getattr(tc, "name", "") or getattr(getattr(tc, "function", None), "name", "")
                        tc_args = getattr(tc, "arguments", {}) or getattr(getattr(tc, "function", None), "arguments", {})
                        if isinstance(tc_args, str):
                            import json

                            try:
                                tc_args = json.loads(tc_args)
                            except json.JSONDecodeError:
                                tc_args = {"raw": tc_args}

                    tool_calls.append(NativeToolCall(id=tc_id, name=tc_name, arguments=tc_args))
        elif (
            entry.entry_type
            in (
                TimelineEntryType.UNKNOWN_TOOL_CALL,
                TimelineEntryType.FAILED_TOOL_CALL,
            )
            and entry.tool_call_id
        ):
            # Tool execution errors with a tool_call_id must be role="tool"
            # so the LLM API can match them to their corresponding tool_calls.
            # Without this, the API rejects with "tool_call_ids did not have response messages".
            role = "tool"
            tool_call_id = entry.tool_call_id
        else:
            # Default: AGENT_RESPONSE, AGENT_THOUGHTS, AGENT_LEARNING, SUB_AGENT_RESPONSE,
            # TODO_LIST, UNKNOWN_TOOL_CALL (without tool_call_id), FAILED_TOOL_CALL (without tool_call_id)
            role = "assistant"

        return NativeMessage(
            role=role,
            content=entry.content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            metadata=entry.metadata.copy() if entry.metadata else {},
            timestamp=entry.timestamp,
        )

    @property
    def native_messages(self) -> list[NativeMessage]:
        """
        Get the list of native messages.

        Returns:
            List of NativeMessage objects in chronological order
        """
        return self._native_messages

    def set_context(self, context: dict[str, Any]) -> None:
        """
        Set or replace the ephemeral runtime context entry.

        Overrides the parent set_context() to also update the native messages list.
        This removes any existing CONTEXT entries from both self.timeline and
        self._native_messages, then adds a fresh one to both.

        Args:
            context: Dictionary with context info (e.g., timestamp, user, timezone)
        """
        # Remove existing CONTEXT native messages
        self._native_messages = [
            msg for msg in self._native_messages if not (msg.role == "system" and msg.metadata.get("ephemeral", False))
        ]

        # Call parent implementation (handles timeline and creates entry)
        super().set_context(context)

        # The parent inserts the context entry at the beginning of self.timeline
        # Get the context entry that was just added
        context_entry = self.timeline[0] if self.timeline else None
        if context_entry and context_entry.entry_type == TimelineEntryType.CONTEXT:
            # Convert to native message and insert at the beginning
            native_msg = self._timeline_entry_to_native_message(context_entry)
            native_msg.metadata["ephemeral"] = True
            self._native_messages.insert(0, native_msg)

    def clear_old_entries(self, before_timestamp: datetime) -> int:
        """
        Remove entries before timestamp from both timeline and native messages.

        Overrides the parent clear_old_entries() to also remove corresponding
        native messages, maintaining consistency between the two lists.

        Args:
            before_timestamp: Remove entries before this timestamp

        Returns:
            Number of entries removed
        """
        original_count = len(self.timeline)

        # Remove from timeline
        self.timeline = [entry for entry in self.timeline if entry.timestamp >= before_timestamp]

        # Remove from native messages
        self._native_messages = [msg for msg in self._native_messages if msg.timestamp >= before_timestamp]

        removed_count = original_count - len(self.timeline)
        return removed_count

    def _get_default_llm_call_fn(self) -> Callable[[str], str] | None:
        """
        Get a default LLM call function using the agent's runtime.

        Returns a function that wraps the prompt string in an LLMMessage
        and calls the agent's runtime.call_llm method.

        Returns:
            Callable that takes a prompt string and returns the LLM response,
            or None if agent or runtime is not available.
        """
        if self._agent is None:
            return None

        runtime = getattr(self._agent, "_runtime", None)
        if runtime is None or not hasattr(runtime, "call_llm"):
            return None

        def default_call_fn(prompt: str) -> str:
            messages = [LLMMessage(role="user", content=prompt)]
            return runtime.call_llm(messages)

        return default_call_fn

    def _get_default_llm_call_async_fn(self) -> Callable[[str], Any] | None:
        """
        Get a default async LLM call function using the agent's runtime.

        Returns a function that wraps the prompt string in an LLMMessage
        and calls the agent's runtime.call_llm_async method.

        Returns:
            Callable that takes a prompt string and returns an awaitable LLM response,
            or None if agent or runtime is not available.
        """
        if self._agent is None:
            return None

        runtime = getattr(self._agent, "_runtime", None)
        if runtime is None or not hasattr(runtime, "call_llm_async"):
            return None

        async def default_call_async_fn(prompt: str) -> str:
            messages = [LLMMessage(role="user", content=prompt)]
            return await runtime.call_llm_async(messages)

        return default_call_async_fn

    def _estimate_native_message_tokens(self, message: NativeMessage) -> int:
        """
        Estimate token count for a single NativeMessage.

        Uses a character-based heuristic (4 characters per token), which is
        a reasonable approximation for most LLM tokenizers.

        Args:
            message: NativeMessage to estimate

        Returns:
            Estimated token count
        """
        # Base content tokens
        total = len(message.content) // 4

        # Add tokens for tool_calls if present
        if message.tool_calls:
            for tc in message.tool_calls:
                # Estimate tokens for tool call structure: id, name, arguments
                total += len(tc.id) // 4
                total += len(tc.name) // 4
                total += len(str(tc.arguments)) // 4

        return total

    def _estimate_native_messages_list_tokens(self, messages: list[NativeMessage]) -> int:
        """
        Estimate token count for a list of NativeMessage objects.

        Args:
            messages: List of NativeMessage objects

        Returns:
            Estimated token count
        """
        total = 0
        for msg in messages:
            try:
                total += self._estimate_native_message_tokens(msg)
            except Exception as e:
                logger.error(f"Error estimating token count for native message: {e}")
                continue
        return total

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
            # Rough estimation: 4 characters per token
            try:
                total += self._estimate_entry_tokens(entry)
            except Exception as e:
                logger.error(f"Error estimating token count for entry: {e}")
                continue
        return int(total)

    def needs_compression(self) -> bool:
        """
        Check if timeline compression is needed.

        Compression is needed when total tokens exceed max_tokens_until_compression.
        Uses native message token counts for more accurate estimation.

        Returns:
            True if compression should be triggered
        """
        if not self._compressed_config.compression_enabled:
            return False

        # Need at least some entries to compress
        if len(self._native_messages) <= self._compressed_config.max_recent_entries_to_keep:
            return False

        # Estimate current token usage using native messages
        current_tokens = self._estimate_native_messages_list_tokens(self._native_messages)
        return current_tokens > self._compressed_config.max_tokens_until_compression

    def get_entries_to_keep_and_compress(self) -> tuple[list[TimelineEntry], list[TimelineEntry]]:
        """
        Determine which entries to keep and which to compress.

        This method now derives its result from native message partitioning to ensure
        consistency. The partitioning is based on native message token estimation
        which is more accurate than TimelineEntry-based estimation.

        Iterates from latest to oldest, keeping entries until:
        - Token count reaches cutoff_when_token_reach, OR
        - Entry count reaches max_recent_entries_to_keep

        Ensures tool_call/tool_result pairs are not split.

        Returns:
            Tuple of (entries_to_keep, entries_to_compress)
        """
        if not self.timeline:
            return [], []

        # Use native message partitioning as the source of truth
        native_to_keep, _ = self.get_native_messages_to_keep_and_compress()

        # The number of entries to keep should match the number of native messages to keep
        # because each TimelineEntry corresponds to one NativeMessage
        entries_to_keep_count = len(native_to_keep)

        # Get entries from the end of timeline (most recent)
        if entries_to_keep_count >= len(self.timeline):
            entries_to_keep = self.timeline[:]
            entries_to_compress = []
        else:
            entries_to_keep = self.timeline[-entries_to_keep_count:] if entries_to_keep_count > 0 else []
            entries_to_compress = self.timeline[:-entries_to_keep_count] if entries_to_keep_count > 0 else self.timeline[:]

        return entries_to_keep, entries_to_compress

    def _ensure_tool_pair_integrity(self, entries: list[TimelineEntry]) -> list[TimelineEntry]:
        """
        Ensure tool_call and tool_result pairs are kept together.

        If entries start with tool results without their tool_calls,
        we need to expand backwards in the original timeline.

        Args:
            entries: List of entries to check

        Returns:
            Entries with complete tool pairs
        """
        if not entries:
            return entries

        # Check if first entries are orphaned tool results
        first_idx = 0
        while first_idx < len(entries) and entries[first_idx].tool_call_id:
            first_idx += 1

        if first_idx == 0:
            # No orphaned tool results at the start
            return entries

        # Find the tool_call for these orphaned results in the original timeline
        timeline_idx = self.timeline.index(entries[0]) if entries[0] in self.timeline else -1
        if timeline_idx <= 0:
            return entries

        # Look backwards in the original timeline for the tool_call
        additional_entries = []
        for i in range(timeline_idx - 1, -1, -1):
            entry = self.timeline[i]
            additional_entries.insert(0, entry)
            if entry.tool_calls:
                # Found the tool_call, stop looking
                break

        return additional_entries + entries

    def get_native_messages_to_keep_and_compress(self) -> tuple[list[NativeMessage], list[NativeMessage]]:
        """
        Determine which native messages to keep and which to compress.

        Iterates from latest to oldest, keeping messages until:
        - Token count reaches cutoff_when_token_reach, OR
        - Message count reaches max_recent_entries_to_keep

        Ensures tool_call/tool_result pairs are not split.

        Returns:
            Tuple of (messages_to_keep, messages_to_compress)
        """
        if not self._native_messages:
            return [], []

        messages_to_keep: list[NativeMessage] = []
        current_tokens = 0
        message_count = 0

        # Iterate from latest to oldest
        for msg in reversed(self._native_messages):
            msg_tokens = self._estimate_native_message_tokens(msg)

            # Check if we've hit our limits
            would_exceed_tokens = (current_tokens + msg_tokens) > self.cutoff_when_token_reach
            would_exceed_entries = message_count >= self.max_recent_entries_to_keep

            if would_exceed_tokens or would_exceed_entries:
                # Check if we need to include this message to keep tool pairs together
                if msg.tool_calls and messages_to_keep:
                    # This is a tool_call message, check if we have its results in kept messages
                    has_orphaned_results = any(
                        m.tool_call_id is not None
                        for m in messages_to_keep
                        if not any(kept.tool_calls for kept in messages_to_keep if kept.timestamp < m.timestamp)
                    )
                    if has_orphaned_results:
                        # Include this tool_call to avoid orphaning results
                        messages_to_keep.insert(0, msg)
                        current_tokens += msg_tokens
                        message_count += 1
                        continue
                break

            messages_to_keep.insert(0, msg)
            current_tokens += msg_tokens
            message_count += 1

        # Ensure we don't break tool_call/tool_result pairs at the boundary
        messages_to_keep = self._ensure_native_message_tool_pair_integrity(messages_to_keep)

        # Everything not kept should be compressed
        kept_set = set(id(m) for m in messages_to_keep)
        messages_to_compress = [m for m in self._native_messages if id(m) not in kept_set]

        return messages_to_keep, messages_to_compress

    def _ensure_native_message_tool_pair_integrity(self, messages: list[NativeMessage]) -> list[NativeMessage]:
        """
        Ensure tool_call and tool_result pairs are kept together for native messages.

        If messages start with tool results without their tool_calls,
        we need to expand backwards in the original native message list.

        Args:
            messages: List of NativeMessage to check

        Returns:
            Messages with complete tool pairs
        """
        if not messages:
            return messages

        # Check if first messages are orphaned tool results
        first_idx = 0
        while first_idx < len(messages) and messages[first_idx].tool_call_id:
            first_idx += 1

        if first_idx == 0:
            # No orphaned tool results at the start
            return messages

        # Find the tool_call for these orphaned results in the original native messages list
        try:
            msg_idx = self._native_messages.index(messages[0])
        except ValueError:
            return messages

        if msg_idx <= 0:
            return messages

        # Look backwards in the original native messages for the tool_call
        additional_messages: list[NativeMessage] = []
        for i in range(msg_idx - 1, -1, -1):
            msg = self._native_messages[i]
            additional_messages.insert(0, msg)
            if msg.tool_calls:
                # Found the tool_call, stop looking
                break

        return additional_messages + messages

    def _estimate_entry_tokens(self, entry: TimelineEntry) -> int:
        """
        Estimate token count for a single entry.

        Args:
            entry: TimelineEntry to estimate

        Returns:
            Estimated token count
        """
        # Rough estimation: 4 characters per token
        return int(len(str(entry.content)) / 4)

    def build_compression_prompt(self) -> str | None:
        """
        Build a prompt for LLM-based compression using Claude Code technique.

        The prompt is designed to create a concise summary that preserves:
        - Key decisions and outcomes
        - Important facts and context
        - Tool calls and their results
        - User preferences and constraints

        Returns:
            Prompt string for summarization, or None if compression not needed
        """
        _, entries_to_compress = self.get_entries_to_keep_and_compress()

        if not entries_to_compress:
            return None

        # Format entries for compression prompt
        formatted_entries = self._format_entries_for_compression(entries_to_compress)

        # Claude Code style compression prompt
        prompt = f"""You are compressing conversation history to preserve important context.

Create a concise summary that captures:
1. Key facts, decisions, and outcomes
2. Important tool calls and their results
3. User requirements and constraints
4. Any ongoing tasks or pending items

The summary should allow the conversation to continue seamlessly without losing critical context.

IMPORTANT: Be concise but comprehensive. Focus on information that would be needed to continue the conversation intelligently.

Conversation history to compress:
{formatted_entries}

Respond with ONLY a JSON object containing the summary:
{{"summary": "Your compressed context summary here"}}"""

        return prompt

    def _format_entries_for_compression(self, entries: list[TimelineEntry]) -> str:
        """
        Format timeline entries for the compression prompt.

        Args:
            entries: List of entries to format

        Returns:
            Formatted string representation
        """
        role_map = {
            TimelineEntryType.USER_MESSAGE: "User",
            TimelineEntryType.AGENT_RESPONSE: "Assistant",
            TimelineEntryType.AGENT_THOUGHTS: "Assistant (thinking)",
            TimelineEntryType.TOOL_CALL: "Tool call",
            TimelineEntryType.RESOURCE_RESULT: "Tool result",
            TimelineEntryType.WORKFLOW_RESULT: "Workflow result",
            TimelineEntryType.SUB_AGENT_RESPONSE: "Sub-agent",
            TimelineEntryType.AGENT_LEARNING: "Learning",
            TimelineEntryType.TIMELINE_SUMMARY: "Previous summary",
            TimelineEntryType.TODO_LIST: "Todo list",
        }

        formatted_parts = []
        for entry in entries:
            # Truncate very long entries
            content = entry.content
            if len(content) > 1000:
                content = content[:1000] + "... [truncated]"

            role = role_map.get(entry.entry_type, entry.entry_type.value)
            formatted_parts.append(f"[{role}] {content}")

        return "\n\n".join(formatted_parts)

    def compress(self) -> int:
        """
        Perform compression on the timeline.

        This method:
        1. Determines entries to keep and compress
        2. Calls LLM to generate summary of entries to compress
        3. Stores compressed context in metadata of oldest kept entry
        4. Removes compressed entries

        Returns:
            Number of entries compressed

        Raises:
            RuntimeError: If LLM call function is not set and no agent runtime available
        """
        # Use provided function or fall back to agent runtime
        llm_call_fn = self._llm_call_fn or self._get_default_llm_call_fn()
        if llm_call_fn is None:
            raise RuntimeError(
                "LLM call function not set and no agent runtime available. "
                "Use set_llm_call_fn() to provide a compression function or ensure an agent with runtime is provided."
            )

        if not self.needs_compression():
            return 0

        entries_to_keep, entries_to_compress = self.get_entries_to_keep_and_compress()

        if not entries_to_compress:
            return 0

        # Build compression prompt
        prompt = self.build_compression_prompt()
        if not prompt:
            return 0

        # Call LLM to get summary
        try:
            response = llm_call_fn(prompt)
            summary = self._extract_summary_from_response(response)
        except Exception as e:
            logger.error(f"Failed to compress timeline: {e}")
            return 0

        if not summary:
            logger.warning("LLM returned empty summary, skipping compression")
            return 0

        # Store compressed context in metadata of oldest kept entry
        compressed_count = self._apply_compression(entries_to_keep, entries_to_compress, summary)

        logger.info(
            f"Compressed {compressed_count} timeline entries",
            compressed_count=compressed_count,
            remaining_entries=len(self.timeline),
            summary_length=len(summary),
        )

        return compressed_count

    async def compress_async(self) -> int:
        """
        Perform compression on the timeline asynchronously.

        Returns:
            Number of entries compressed

        Raises:
            RuntimeError: If async LLM call function is not set and no agent runtime available
        """
        # Use provided function or fall back to agent runtime
        llm_call_async_fn = self._llm_call_async_fn or self._get_default_llm_call_async_fn()
        if llm_call_async_fn is None:
            raise RuntimeError(
                "Async LLM call function not set and no agent runtime available. "
                "Use set_llm_call_async_fn() to provide a compression function or ensure an agent with runtime is provided."
            )

        if not self.needs_compression():
            return 0

        entries_to_keep, entries_to_compress = self.get_entries_to_keep_and_compress()

        if not entries_to_compress:
            return 0

        # Build compression prompt
        prompt = self.build_compression_prompt()
        if not prompt:
            return 0

        # Call LLM to get summary
        try:
            response = await llm_call_async_fn(prompt)
            summary = self._extract_summary_from_response(response)
        except Exception as e:
            logger.error(f"Failed to compress timeline: {e}")
            return 0

        if not summary:
            logger.warning("LLM returned empty summary, skipping compression")
            return 0

        # Store compressed context in metadata of oldest kept entry
        compressed_count = self._apply_compression(entries_to_keep, entries_to_compress, summary)

        logger.info(
            f"Compressed {compressed_count} timeline entries",
            compressed_count=compressed_count,
            remaining_entries=len(self.timeline),
            summary_length=len(summary),
        )

        return compressed_count

    def _apply_compression(
        self,
        entries_to_keep: list[TimelineEntry],
        entries_to_compress: list[TimelineEntry],
        summary: str,
    ) -> int:
        """
        Apply compression by storing summary and updating timeline and native messages.

        This method updates both the legacy TimelineEntry list (self.timeline) and the
        native message list (self._native_messages) to maintain consistency.

        For native messages:
        - Creates a summary NativeMessage with role='system'
        - Preserves recent NativeMessages (within max_recent_entries_to_keep)
        - Removes compressed native messages

        Args:
            entries_to_keep: Entries to preserve
            entries_to_compress: Entries being compressed
            summary: The compressed summary

        Returns:
            Number of entries compressed
        """
        compressed_count = len(entries_to_compress)
        compression_timestamp = datetime.now()

        # Calculate how many native messages to keep
        # We need to keep messages corresponding to entries_to_keep
        native_messages_to_keep_count = len(entries_to_keep)

        # Create summary as a NativeMessage with role='system'
        summary_native_message = NativeMessage(
            role="system",
            content=f"[SUMMARY] {summary}",
            metadata={
                COMPRESSED_CONTEXT_KEY: summary,
                COMPRESSION_TIMESTAMP_KEY: compression_timestamp.isoformat(),
                COMPRESSED_ENTRIES_COUNT_KEY: compressed_count,
            },
            timestamp=compression_timestamp,
        )

        if not entries_to_keep:
            # Edge case: create a summary entry if nothing to keep
            summary_entry = TimelineEntry(
                entry_type=TimelineEntryType.TIMELINE_SUMMARY,
                content=summary,
                timestamp=entries_to_compress[0].timestamp if entries_to_compress else compression_timestamp,
                metadata={
                    COMPRESSED_CONTEXT_KEY: summary,
                    COMPRESSION_TIMESTAMP_KEY: compression_timestamp.isoformat(),
                    COMPRESSED_ENTRIES_COUNT_KEY: compressed_count,
                },
            )
            self.timeline = [summary_entry]

            # Update native messages: only the summary
            self._native_messages = [summary_native_message]

            return compressed_count

        # Store compressed context in metadata of the oldest kept entry
        oldest_kept = entries_to_keep[0]
        oldest_kept.metadata[COMPRESSED_CONTEXT_KEY] = summary
        oldest_kept.metadata[COMPRESSION_TIMESTAMP_KEY] = compression_timestamp.isoformat()
        oldest_kept.metadata[COMPRESSED_ENTRIES_COUNT_KEY] = compressed_count

        # Update timeline to only contain kept entries
        self.timeline = entries_to_keep

        # Update native messages: summary + recent messages
        # Get the native messages corresponding to kept entries (from the end)
        recent_native_messages = self._native_messages[-native_messages_to_keep_count:] if native_messages_to_keep_count > 0 else []

        # Also update metadata on the first kept native message
        if recent_native_messages:
            recent_native_messages[0].metadata[COMPRESSED_CONTEXT_KEY] = summary
            recent_native_messages[0].metadata[COMPRESSION_TIMESTAMP_KEY] = compression_timestamp.isoformat()
            recent_native_messages[0].metadata[COMPRESSED_ENTRIES_COUNT_KEY] = compressed_count

        # New native messages list: summary + kept native messages
        self._native_messages = [summary_native_message] + recent_native_messages

        return compressed_count

    def _extract_summary_from_response(self, response: str) -> str | None:
        """
        Extract summary from LLM response.

        Handles both JSON format {"summary": "..."} and plain text.

        Args:
            response: LLM response string

        Returns:
            Extracted summary or None if extraction fails
        """
        import json

        response = response.strip()

        # Try JSON extraction first
        try:
            # Handle potential markdown code blocks
            if response.startswith("```"):
                # Extract content between code blocks
                lines = response.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block:
                        json_lines.append(line)
                response = "\n".join(json_lines)

            data = json.loads(response)
            if isinstance(data, dict) and "summary" in data:
                return data["summary"]
        except json.JSONDecodeError:
            pass

        # If not JSON, use the response as-is (but clean it up)
        if response and not response.startswith("{"):
            return response

        return None

    def get_compressed_context(self) -> str | None:
        """
        Get the compressed context from the timeline if available.

        Looks for compressed context metadata in both native messages and
        timeline entries (for backward compatibility).

        Returns:
            Compressed context string or None if not available
        """
        # First check native messages (preferred source after compression)
        for msg in self._native_messages:
            if COMPRESSED_CONTEXT_KEY in msg.metadata:
                return msg.metadata[COMPRESSED_CONTEXT_KEY]

        # Fall back to timeline entries (for backward compatibility)
        for entry in self.timeline:
            if COMPRESSED_CONTEXT_KEY in entry.metadata:
                return entry.metadata[COMPRESSED_CONTEXT_KEY]
        return None

    def has_compressed_context(self) -> bool:
        """
        Check if timeline has compressed context.

        Returns:
            True if compressed context exists in any entry's metadata
        """
        return self.get_compressed_context() is not None

    def compress_old_entries(self, summary: str) -> int:
        """
        Compress old timeline entries into a summary entry.

        This method implements the TimelineProtocol interface for compression.
        It replaces old entries with a summary, updating both self.timeline
        and self._native_messages to maintain consistency.

        For CompressedTimeline, this method uses the same logic as _apply_compression()
        but accepts an externally provided summary (e.g., from LLM-based summarization).

        Args:
            summary: The summary text to use for the compressed entries

        Returns:
            Number of entries that were compressed
        """
        entries_to_keep, entries_to_compress = self.get_entries_to_keep_and_compress()

        if not entries_to_compress:
            return 0

        # Apply compression with the provided summary
        return self._apply_compression(entries_to_keep, entries_to_compress, summary)

    def get_entries_for_compression(self) -> list[TimelineEntry]:
        """
        Get the entries that would be compressed.

        This method implements the TimelineProtocol interface and returns
        the entries that would be replaced by a summary during compression.
        It uses the CompressedTimeline's own partitioning logic which respects
        token limits and recent entry counts.

        Returns:
            List of old entries that would be replaced by a summary
        """
        _, entries_to_compress = self.get_entries_to_keep_and_compress()
        return entries_to_compress

    def to_llm_messages(
        self,
        max_tokens: int | None = None,
        default_role: str = "user",  # noqa: ARG002 - kept for TimelineProtocol compatibility
        separate_latest_user: bool = False,
    ) -> list[LLMMessage]:
        """
        Convert native messages to LLM messages for provider consumption.

        This method returns individual messages from the native storage, preserving
        the original message structure. Unlike the parent implementation that works
        with TimelineEntry objects, this directly uses the NativeMessage list.

        If compression has occurred:
        - A summary system message is prepended
        - Recent individual messages follow (not a single compressed blob)

        Token limiting is applied via sliding window on native messages, keeping
        tool_call/tool_result pairs together.

        Args:
            max_tokens: Maximum tokens to include (overrides max_context_tokens)
            default_role: Default role for entries without specific mapping. Unused
                in this implementation since NativeMessage has explicit roles, but
                kept for TimelineProtocol compatibility.
            separate_latest_user: If True, separates latest user message

        Returns:
            List of LLMMessage objects in chronological order
        """
        token_limit = max_tokens or self.max_context_tokens

        # Convert native messages to LLMMessage
        messages = [msg.to_llm_message() for msg in self._native_messages]

        # If we have compressed context, prepend it as a system message
        compressed_context = self.get_compressed_context()
        if compressed_context:
            # Check if we already have a summary message (to avoid duplication)
            has_summary = any(
                msg.content.startswith("[Previous context summary]") or msg.content.startswith("[SUMMARY]") for msg in messages
            )

            if not has_summary:
                summary_message = LLMMessage(
                    role="system",
                    content=f"[Previous context summary] {compressed_context}",
                )
                # Insert at the beginning (or after other system messages)
                insert_idx = 0
                for i, msg in enumerate(messages):
                    if msg.role == "system":
                        insert_idx = i + 1
                    else:
                        break
                messages.insert(insert_idx, summary_message)

        # Handle separate_latest_user: separate the latest user message
        if separate_latest_user and messages:
            # Find the latest user message
            latest_user_idx = None
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].role == "user":
                    latest_user_idx = i
                    break

            if latest_user_idx is not None:
                latest_user_msg = messages[latest_user_idx]
                context_messages = messages[:latest_user_idx] + messages[latest_user_idx + 1 :]

                # Apply token limit to context
                if self._estimate_native_messages_tokens(context_messages) > token_limit:
                    context_messages = self._apply_token_limit_to_messages(context_messages, token_limit)

                # Append latest user message at the end
                context_messages.append(latest_user_msg)
                return context_messages

        # Apply token limit if needed
        if self._estimate_native_messages_tokens(messages) > token_limit:
            messages = self._apply_token_limit_to_messages(messages, token_limit)

        return messages

    def _estimate_native_messages_tokens(self, messages: list[LLMMessage]) -> int:
        """
        Estimate token count for a list of LLMMessage objects.

        Args:
            messages: List of LLMMessage objects

        Returns:
            Estimated token count
        """
        total = 0
        for msg in messages:
            # Rough estimation: 4 characters per token
            total += len(msg.content) // 4
            # Add tokens for tool_calls if present
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    if isinstance(tc, dict):
                        total += len(str(tc)) // 4
                    else:
                        total += len(str(tc)) // 4
        return total

    def _apply_token_limit_to_messages(self, messages: list[LLMMessage], max_tokens: int) -> list[LLMMessage]:
        """
        Apply token limit to messages using sliding window approach.

        Preserves message integrity by keeping tool_call/tool_result pairs together.
        Always includes the most recent messages and any system messages.

        Args:
            messages: List of LLMMessage objects
            max_tokens: Maximum tokens to include

        Returns:
            List of LLMMessage objects within token limit
        """
        if not messages:
            return []

        # Group messages into atomic units that must stay together:
        # - assistant with tool_calls + following tool results
        # - single messages (user, system, assistant without tool_calls)
        groups: list[list[LLMMessage]] = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            if msg.role == "assistant" and msg.tool_calls:
                # Start a group with assistant + all following tool results
                group = [msg]
                i += 1
                while i < len(messages) and messages[i].role == "tool":
                    group.append(messages[i])
                    i += 1
                groups.append(group)
            else:
                groups.append([msg])
                i += 1

        # Collect system message groups (they should always be included)
        system_groups: list[list[LLMMessage]] = []
        non_system_groups: list[list[LLMMessage]] = []
        for group in groups:
            if group[0].role == "system":
                system_groups.append(group)
            else:
                non_system_groups.append(group)

        # Calculate tokens for system messages
        system_tokens = sum(self._estimate_native_messages_tokens(g) for g in system_groups)
        available_tokens = max_tokens - system_tokens

        # Build result from most recent non-system groups, respecting token limit
        result_groups: list[list[LLMMessage]] = []
        current_tokens = 0

        for group in reversed(non_system_groups):
            group_tokens = self._estimate_native_messages_tokens(group)

            if current_tokens + group_tokens > available_tokens:
                # Always include at least the most recent group
                if not result_groups:
                    result_groups.insert(0, group)
                    current_tokens += group_tokens
                break

            result_groups.insert(0, group)
            current_tokens += group_tokens

        # Reconstruct final message list: system messages first, then selected groups
        result: list[LLMMessage] = []
        for group in system_groups:
            result.extend(group)
        for group in result_groups:
            result.extend(group)

        return result

    def read_since(self, checkpoint: int) -> Iterator[TimelineEntry]:
        """
        Read timeline entries since checkpoint, with compression-aware loading.

        This override ensures that when loading from repository, we leverage
        compressed context metadata to avoid loading unnecessary old entries.

        Args:
            checkpoint: Starting index for reading entries

        Yields:
            TimelineEntry objects since checkpoint
        """
        # First, get all entries using parent method
        all_entries = list(super().read_since(checkpoint))

        # Find the first entry with compressed context (from the end)
        cutoff_idx = 0
        for i, entry in enumerate(reversed(all_entries)):
            if COMPRESSED_CONTEXT_KEY in entry.metadata:
                cutoff_idx = len(all_entries) - i - 1
                break

        # Yield entries from the cutoff point
        for entry in all_entries[cutoff_idx:]:
            yield entry

    def save(self, session_id: str) -> None:
        """
        Save timeline for a session, including native messages.

        This override extends the parent save to also persist the native messages
        in the same JSON file. The native messages are stored in a separate
        "native_messages" key for backward compatibility.

        Ephemeral entries (like CONTEXT) are excluded from persistence.

        Args:
            session_id: Session identifier
        """
        if self._repository is None:
            raise ValueError("Cannot save timeline: repository is None. Initialize Timeline with repository or agent.")

        # Filter out ephemeral entries before saving
        persistent_entries = [e for e in self.timeline if not e.ephemeral]

        # Filter out ephemeral native messages (those corresponding to CONTEXT entries)
        persistent_native_messages = [
            msg for msg in self._native_messages if not (msg.role == "system" and msg.metadata.get("ephemeral", False))
        ]

        # Use the repository's save method for TimelineEntry
        self._repository.save(session_id, persistent_entries)

        # Now also save native messages to the same file
        # We need to access the repository's internal path to update the JSON
        if hasattr(self._repository, "_events_path"):
            import json
            from pathlib import Path

            events_path = self._repository._events_path
            session_folder = Path(events_path) / session_id
            timeline_file = session_folder / "timeline.json"

            if timeline_file.exists():
                # Read existing data and add native_messages
                with open(timeline_file) as f:
                    timeline_data = json.load(f)

                # Add native messages to the saved data
                timeline_data["native_messages"] = [msg.to_dict() for msg in persistent_native_messages]

                # Write back
                with open(timeline_file, "w") as f:
                    json.dump(timeline_data, f, indent=2)

        logger.info(
            f"Saved compressed timeline with {len(persistent_entries)} entries "
            f"and {len(persistent_native_messages)} native messages for session {session_id}"
        )

    def load_from_entries(
        self,
        entries: list[TimelineEntry] | list[dict[str, Any]],
        native_messages: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Load timeline from entries, supporting both legacy and native message formats.

        This method handles loading from:
        1. Legacy format: list[TimelineEntry] - converted to native on load
        2. Native format: list[dict] with 'role' field - loaded as NativeMessage
        3. Mixed format: entries + optional native_messages list

        Format detection is via presence of 'role' field (native) vs 'type' field (legacy).

        Args:
            entries: List of TimelineEntry objects or dicts (legacy format)
            native_messages: Optional list of native message dicts (new format)
        """
        if not entries and not native_messages:
            self.timeline = []
            self._native_messages = []
            return

        # Check if entries are in native format (dicts with 'role' key) or legacy format (dicts with 'type' key)
        first_entry = entries[0] if entries else None

        if isinstance(first_entry, dict):
            # Check for native format indicator
            if "role" in first_entry and "type" not in first_entry:
                # Native format - load as NativeMessage directly
                self._load_from_native_format(entries)  # type: ignore[arg-type]
                return

        # Legacy format or TimelineEntry objects - use original loading logic
        # Convert dicts to TimelineEntry if needed
        timeline_entries: list[TimelineEntry] = []
        for entry in entries:
            if isinstance(entry, dict):
                timeline_entries.append(TimelineEntry.from_dict(entry))
            else:
                timeline_entries.append(entry)

        # Check if we have native_messages separately provided
        if native_messages:
            # Load timeline entries using legacy logic
            self._load_timeline_entries_legacy(timeline_entries)
            # Load native messages directly
            self._native_messages = [NativeMessage.from_dict(msg) for msg in native_messages]
            logger.info(
                f"Loaded {len(self.timeline)} timeline entries with {len(self._native_messages)} native messages from separate storage"
            )
        else:
            # Pure legacy format - load entries and convert to native
            self._load_timeline_entries_legacy(timeline_entries)
            # Convert each entry to native message
            self._native_messages = [self._timeline_entry_to_native_message(entry) for entry in self.timeline]
            logger.info(f"Loaded and converted {len(self.timeline)} legacy timeline entries to native format")

    def _load_timeline_entries_legacy(self, entries: list[TimelineEntry]) -> None:
        """
        Load timeline entries using the legacy compression-aware logic.

        This implements the original load_from_entries optimization:
        - Iterates through entries from most recent
        - When it finds an entry with compressed context metadata, stops there
        - Uses the compressed context to represent older history

        Args:
            entries: List of TimelineEntry objects to load
        """
        if not entries:
            self.timeline = []
            return

        # Look for entry with compressed context, starting from most recent
        # We want to keep entries from the one with compressed context onwards
        entries_to_load = []
        found_compressed = False

        for entry in reversed(entries):
            entries_to_load.insert(0, entry)
            if COMPRESSED_CONTEXT_KEY in entry.metadata:
                found_compressed = True
                break

        # If we found compressed context, we only need entries from that point
        # Otherwise, load all entries
        if found_compressed:
            self.timeline = entries_to_load
            logger.info(
                f"Loaded {len(entries_to_load)} entries with compressed context "
                f"(skipped {len(entries) - len(entries_to_load)} older entries)"
            )
        else:
            self.timeline = entries
            logger.info(f"Loaded all {len(entries)} entries (no compressed context found)")

    def _load_from_native_format(self, native_data: list[dict[str, Any]]) -> None:
        """
        Load timeline from native message format.

        When loading native format, we:
        1. Load messages directly as NativeMessage
        2. Reconstruct TimelineEntry objects for backward compatibility

        Args:
            native_data: List of native message dicts
        """
        # Load native messages directly
        self._native_messages = []
        entries_to_load: list[NativeMessage] = []
        found_compressed = False

        # Look for message with compressed context, starting from most recent
        for msg_dict in reversed(native_data):
            msg = NativeMessage.from_dict(msg_dict)
            entries_to_load.insert(0, msg)
            if COMPRESSED_CONTEXT_KEY in msg.metadata:
                found_compressed = True
                break

        if found_compressed:
            self._native_messages = entries_to_load
            logger.info(
                f"Loaded {len(entries_to_load)} native messages with compressed context "
                f"(skipped {len(native_data) - len(entries_to_load)} older messages)"
            )
        else:
            self._native_messages = [NativeMessage.from_dict(d) for d in native_data]
            logger.info(f"Loaded all {len(native_data)} native messages (no compressed context found)")

        # Reconstruct TimelineEntry for backward compatibility
        self.timeline = [self._native_message_to_timeline_entry(msg) for msg in self._native_messages]

    def _native_message_to_timeline_entry(self, msg: NativeMessage) -> TimelineEntry:
        """
        Convert a NativeMessage back to TimelineEntry for backward compatibility.

        Args:
            msg: NativeMessage to convert

        Returns:
            TimelineEntry representation
        """
        # Determine entry type from role and content
        entry_type: TimelineEntryType
        tool_calls: list[dict[str, Any]] | None = None
        tool_call_id: str | None = msg.tool_call_id

        if msg.role == "user":
            entry_type = TimelineEntryType.USER_MESSAGE
        elif msg.role == "system":
            # Check if it's a summary or context
            if msg.content.startswith("[SUMMARY]") or COMPRESSED_CONTEXT_KEY in msg.metadata:
                entry_type = TimelineEntryType.TIMELINE_SUMMARY
            else:
                entry_type = TimelineEntryType.CONTEXT
        elif msg.role == "tool":
            entry_type = TimelineEntryType.RESOURCE_RESULT
        elif msg.role == "assistant":
            if msg.tool_calls:
                entry_type = TimelineEntryType.TOOL_CALL
                # Convert NativeToolCall to dict format
                tool_calls = [tc.to_dict() for tc in msg.tool_calls]
            else:
                entry_type = TimelineEntryType.AGENT_RESPONSE
        else:
            entry_type = TimelineEntryType.AGENT_RESPONSE

        return TimelineEntry(
            entry_type=entry_type,
            content=msg.content,
            timestamp=msg.timestamp,
            metadata=msg.metadata.copy(),
            tool_call_id=tool_call_id,
            tool_calls=tool_calls,
        )

    # Type aliases for provider-specific message formats
    OpenAIMessage = dict[str, Any]
    AnthropicMessage = dict[str, Any]

    def to_openai_messages(
        self,
        max_tokens: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Convert native messages to OpenAI API message format.

        OpenAI message format:
        - System: {"role": "system", "content": "..."}
        - User: {"role": "user", "content": "..."}
        - Assistant: {"role": "assistant", "content": "...", "tool_calls": [...]}
        - Tool: {"role": "tool", "tool_call_id": "...", "content": "..."}

        Tool calls format:
        - {"id": "...", "type": "function", "function": {"name": "...", "arguments": "{...}"}}

        Args:
            max_tokens: Maximum tokens to include (applies sliding window)

        Returns:
            List of OpenAI-formatted message dicts
        """
        import json

        # Get LLM messages (applies token limiting and handles compressed context)
        llm_messages = self.to_llm_messages(max_tokens=max_tokens)

        openai_messages: list[dict[str, Any]] = []
        for msg in llm_messages:
            if msg.role == "system":
                openai_messages.append({"role": "system", "content": msg.content})
            elif msg.role == "user":
                openai_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "tool":
                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": msg.content,
                    }
                )
            elif msg.role == "assistant":
                if msg.tool_calls:
                    # Format tool_calls for OpenAI API
                    formatted_tool_calls = []
                    for tc in msg.tool_calls:
                        if isinstance(tc, dict):
                            tc_id = tc.get("id", "")
                            tc_name = tc.get("name", "")
                            tc_args = tc.get("arguments", {})
                        else:
                            tc_id = getattr(tc, "id", "")
                            tc_name = getattr(tc, "name", "")
                            tc_args = getattr(tc, "arguments", {})

                        # OpenAI requires arguments as JSON string
                        if isinstance(tc_args, dict):
                            tc_args = json.dumps(tc_args)
                        elif not isinstance(tc_args, str):
                            tc_args = str(tc_args)

                        formatted_tool_calls.append(
                            {
                                "id": tc_id,
                                "type": "function",
                                "function": {
                                    "name": tc_name,
                                    "arguments": tc_args,
                                },
                            }
                        )
                    openai_messages.append(
                        {
                            "role": "assistant",
                            "content": msg.content or None,
                            "tool_calls": formatted_tool_calls,
                        }
                    )
                else:
                    openai_messages.append({"role": "assistant", "content": msg.content})

        return openai_messages

    def to_anthropic_messages(
        self,
        max_tokens: int | None = None,
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """
        Convert native messages to Anthropic API message format.

        Anthropic message format differs from OpenAI:
        - System message is returned separately (not in messages array)
        - User: {"role": "user", "content": "..."} or {"role": "user", "content": [{"type": "text", "text": "..."}]}
        - Assistant: {"role": "assistant", "content": "..."} or with content blocks
        - Tool use: {"role": "assistant", "content": [{"type": "text", "text": "..."}, {"type": "tool_use", "id": "...", "name": "...", "input": {...}}]}
        - Tool result: {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "...", "content": "..."}]}

        Note: Consecutive tool results are combined into a single user message.

        Args:
            max_tokens: Maximum tokens to include (applies sliding window)

        Returns:
            Tuple of (system_message, messages) where system_message is the content
            of the system message (or None) and messages is a list of Anthropic-formatted
            message dicts.
        """
        # Get LLM messages (applies token limiting and handles compressed context)
        llm_messages = self.to_llm_messages(max_tokens=max_tokens)

        system_message: str | None = None
        anthropic_messages: list[dict[str, Any]] = []

        for msg in llm_messages:
            if msg.role == "system":
                # Anthropic handles system message separately
                # Combine multiple system messages if present
                if system_message is None:
                    system_message = msg.content
                else:
                    system_message = f"{system_message}\n\n{msg.content}"
            elif msg.role == "user":
                anthropic_messages.append({"role": "user", "content": msg.content})
            elif msg.role == "tool":
                # Tool result - Anthropic uses tool_result content block in user message
                tool_result_block = {
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id,
                    "content": msg.content,
                }
                # Check if the last message is already a user message with tool_result blocks
                # If so, append to it (for parallel tool results)
                if (
                    anthropic_messages
                    and anthropic_messages[-1].get("role") == "user"
                    and isinstance(anthropic_messages[-1].get("content"), list)
                    and anthropic_messages[-1]["content"]
                    and anthropic_messages[-1]["content"][0].get("type") == "tool_result"
                ):
                    # Append to existing tool results
                    anthropic_messages[-1]["content"].append(tool_result_block)
                else:
                    # Create new user message with tool_result
                    anthropic_messages.append(
                        {
                            "role": "user",
                            "content": [tool_result_block],
                        }
                    )
            elif msg.role == "assistant":
                if msg.tool_calls:
                    # Format as content blocks with tool_use
                    content_blocks: list[dict[str, Any]] = []
                    if msg.content:
                        content_blocks.append({"type": "text", "text": msg.content})
                    for tc in msg.tool_calls:
                        if isinstance(tc, dict):
                            tc_id = tc.get("id", "")
                            tc_name = tc.get("name", "")
                            tc_input = tc.get("arguments", {})
                        else:
                            tc_id = getattr(tc, "id", "")
                            tc_name = getattr(tc, "name", "")
                            tc_input = getattr(tc, "arguments", {})

                        # Anthropic expects input as dict, not string
                        if isinstance(tc_input, str):
                            import json

                            try:
                                tc_input = json.loads(tc_input)
                            except json.JSONDecodeError:
                                tc_input = {"raw": tc_input}

                        content_blocks.append(
                            {
                                "type": "tool_use",
                                "id": tc_id,
                                "name": tc_name,
                                "input": tc_input,
                            }
                        )
                    anthropic_messages.append(
                        {
                            "role": "assistant",
                            "content": content_blocks,
                        }
                    )
                else:
                    anthropic_messages.append({"role": "assistant", "content": msg.content})

        return system_message, anthropic_messages
