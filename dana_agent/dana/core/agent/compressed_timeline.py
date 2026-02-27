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

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import json
from typing import TYPE_CHECKING, Any

from structlog import get_logger

from dana.common.llm.types import LLMMessage
from dana.core.agent.compression_engine import CompressionMixin
from dana.core.agent.native_message import (
    COMPRESSED_CONTEXT_KEY,
    COMPRESSED_ENTRIES_COUNT_KEY,
    COMPRESSION_TIMESTAMP_KEY,
    NativeMessage,
    NativeMessageRole,
    NativeToolCall,
)
from dana.core.agent.provider_messages import ProviderMessagesMixin
from dana.core.agent.timeline import (
    Timeline,
    TimelineConfig,
    TimelineEntry,
    TimelineEntryType,
)
from dana.core.agent.timeline_serializer import TimelineSerializerMixin
from dana.repositories.repository_factory import DEFAULT_REPOSITORY_FACTORY, RepositoryFactory


if TYPE_CHECKING:
    from dana.core.agent.base_agent import BaseAgent

logger = get_logger()

# Re-export type alias so existing imports still work
# (e.g. `from dana.core.agent.compressed_timeline import NativeMessageRole`)
__all__ = [
    "CompressedTimeline",
    "CompressedTimelineConfig",
    "NativeMessage",
    "NativeMessageRole",
    "NativeToolCall",
    "COMPRESSED_CONTEXT_KEY",
    "COMPRESSION_TIMESTAMP_KEY",
    "COMPRESSED_ENTRIES_COUNT_KEY",
    "CompressionMixin",
    "TimelineSerializerMixin",
    "ProviderMessagesMixin",
]


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


class CompressedTimeline(CompressionMixin, TimelineSerializerMixin, ProviderMessagesMixin, Timeline):
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
        compression_enabled: bool = True,
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
            compression_enabled: Whether compression is enabled (default True).
                Set to False to disable compression and behave like plain Timeline.
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
            compression_enabled=compression_enabled,
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

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # LLM call function setters
    # ------------------------------------------------------------------

    def set_llm_call_fn(self, fn: Callable[[str], str]) -> None:
        """Set the synchronous LLM call function."""
        self._llm_call_fn = fn

    def set_llm_call_async_fn(self, fn: Callable[[str], Any]) -> None:
        """Set the async LLM call function."""
        self._llm_call_async_fn = fn

    # ------------------------------------------------------------------
    # Entry management
    # ------------------------------------------------------------------

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
        # Compare by .value (string) instead of enum identity to handle the case where
        # the same TimelineEntryType enum is loaded under two module paths
        # (e.g., dana.core.agent.timeline vs dana_agent.dana.core.agent.timeline)
        # due to namespace package merging with editable installs.
        entry_type_value = entry.entry_type.value if hasattr(entry.entry_type, "value") else str(entry.entry_type)

        if entry_type_value == TimelineEntryType.USER_MESSAGE.value:
            role = "user"
        elif entry_type_value in (
            TimelineEntryType.TIMELINE_SUMMARY.value,
            TimelineEntryType.CONTEXT.value,
        ):
            role = "system"
        elif entry_type_value in (
            TimelineEntryType.RESOURCE_RESULT.value,
            TimelineEntryType.WORKFLOW_RESULT.value,
        ):
            role = "tool"
            tool_call_id = entry.tool_call_id
        elif entry_type_value == TimelineEntryType.TOOL_CALL.value:
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
                            try:
                                tc_args = json.loads(tc_args)
                            except json.JSONDecodeError:
                                tc_args = {"raw": tc_args}

                    tool_calls.append(NativeToolCall(id=tc_id, name=tc_name, arguments=tc_args))
        elif (
            entry_type_value
            in (
                TimelineEntryType.UNKNOWN_TOOL_CALL.value,
                TimelineEntryType.FAILED_TOOL_CALL.value,
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

    # ------------------------------------------------------------------
    # Native messages property
    # ------------------------------------------------------------------

    @property
    def native_messages(self) -> list[NativeMessage]:
        """
        Get the list of native messages.

        Returns:
            List of NativeMessage objects in chronological order
        """
        return self._native_messages

    # ------------------------------------------------------------------
    # Context management
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Default LLM call function helpers (used by CompressionMixin)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Token estimation (used by both CompressionMixin and ProviderMessagesMixin)
    # ------------------------------------------------------------------

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
