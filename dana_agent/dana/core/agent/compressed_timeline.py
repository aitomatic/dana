"""
Compressed Timeline with intelligent context management.

This module provides a Timeline subclass that implements progressive compression
using LLM-based summarization, similar to Claude Code's compression technique.

Key features:
- Token-based compression triggers
- Stores compressed context in entry metadata for efficient loading
- Progressive compression that preserves recent context
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

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


# Metadata keys for compressed context storage
COMPRESSED_CONTEXT_KEY = "compressed_context"
COMPRESSION_TIMESTAMP_KEY = "compression_timestamp"
COMPRESSED_ENTRIES_COUNT_KEY = "compressed_entries_count"


@dataclass
class CompressedTimelineConfig(TimelineConfig):
    """Configuration for compressed timeline with enhanced context management."""

    # Maximum tokens before compression is triggered
    max_tokens_until_compression: int = 32000

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
        max_tokens_until_compression: int = 32000,
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

        Returns:
            True if compression should be triggered
        """
        if not self._compressed_config.compression_enabled:
            return False

        # Need at least some entries to compress
        if len(self.timeline) <= self._compressed_config.max_recent_entries_to_keep:
            return False

        # Estimate current token usage
        current_tokens = self._estimate_entries_tokens(self.timeline)
        return current_tokens > self._compressed_config.max_tokens_until_compression

    def get_entries_to_keep_and_compress(self) -> tuple[list[TimelineEntry], list[TimelineEntry]]:
        """
        Determine which entries to keep and which to compress.

        Iterates from latest to oldest, keeping entries until:
        - Token count reaches cutoff_when_token_reach, OR
        - Entry count reaches max_recent_entries_to_keep

        Ensures tool_call/tool_result pairs are not split.

        Returns:
            Tuple of (entries_to_keep, entries_to_compress)
        """
        if not self.timeline:
            return [], []

        entries_to_keep: list[TimelineEntry] = []
        current_tokens = 0
        entry_count = 0

        # Iterate from latest to oldest
        for entry in reversed(self.timeline):
            entry_tokens = self._estimate_entry_tokens(entry)

            # Check if we've hit our limits
            would_exceed_tokens = (current_tokens + entry_tokens) > self.cutoff_when_token_reach
            would_exceed_entries = entry_count >= self.max_recent_entries_to_keep

            if would_exceed_tokens or would_exceed_entries:
                # Check if we need to include this entry to keep tool pairs together
                if entry.tool_calls and entries_to_keep:
                    # This is a tool_call entry, check if we have its results in kept entries
                    has_orphaned_results = any(
                        e.tool_call_id is not None
                        for e in entries_to_keep
                        if not any(kept.tool_calls for kept in entries_to_keep if kept.timestamp < e.timestamp)
                    )
                    if has_orphaned_results:
                        # Include this tool_call to avoid orphaning results
                        entries_to_keep.insert(0, entry)
                        current_tokens += entry_tokens
                        entry_count += 1
                        continue
                break

            entries_to_keep.insert(0, entry)
            current_tokens += entry_tokens
            entry_count += 1

        # Ensure we don't break tool_call/tool_result pairs at the boundary
        entries_to_keep = self._ensure_tool_pair_integrity(entries_to_keep)

        # Everything not kept should be compressed
        kept_set = set(id(e) for e in entries_to_keep)
        entries_to_compress = [e for e in self.timeline if id(e) not in kept_set]

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
        Apply compression by storing summary and updating timeline.

        Args:
            entries_to_keep: Entries to preserve
            entries_to_compress: Entries being compressed
            summary: The compressed summary

        Returns:
            Number of entries compressed
        """
        compressed_count = len(entries_to_compress)

        if not entries_to_keep:
            # Edge case: create a summary entry if nothing to keep
            summary_entry = TimelineEntry(
                entry_type=TimelineEntryType.TIMELINE_SUMMARY,
                content=summary,
                timestamp=entries_to_compress[0].timestamp if entries_to_compress else datetime.now(),
                metadata={
                    COMPRESSED_CONTEXT_KEY: summary,
                    COMPRESSION_TIMESTAMP_KEY: datetime.now().isoformat(),
                    COMPRESSED_ENTRIES_COUNT_KEY: compressed_count,
                },
            )
            self.timeline = [summary_entry]
            return compressed_count

        # Store compressed context in metadata of the oldest kept entry
        oldest_kept = entries_to_keep[0]
        oldest_kept.metadata[COMPRESSED_CONTEXT_KEY] = summary
        oldest_kept.metadata[COMPRESSION_TIMESTAMP_KEY] = datetime.now().isoformat()
        oldest_kept.metadata[COMPRESSED_ENTRIES_COUNT_KEY] = compressed_count

        # Update timeline to only contain kept entries
        self.timeline = entries_to_keep

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

        Looks for compressed context metadata in timeline entries.

        Returns:
            Compressed context string or None if not available
        """
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

    def to_llm_messages(
        self,
        max_tokens: int | None = None,
        default_role: str = "user",
        separate_latest_user: bool = False,
    ) -> list[LLMMessage]:
        """
        Convert timeline entries to LLM messages, including compressed context.

        If compressed context exists in the timeline, it will be prepended
        as a system message containing the conversation history summary.

        Args:
            max_tokens: Maximum tokens to include (overrides max_context_tokens)
            default_role: Default role for entries without specific mapping
            separate_latest_user: If True, separates latest user message

        Returns:
            List of LLMMessage objects in chronological order
        """
        # Get base messages from parent
        messages = super().to_llm_messages(max_tokens, default_role, separate_latest_user)

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
                # Insert after any existing system messages (like CONTEXT)
                insert_idx = 0
                for i, msg in enumerate(messages):
                    if msg.role == "system":
                        insert_idx = i + 1
                    else:
                        break
                messages.insert(insert_idx, summary_message)

        return messages

    def load_from_entries(self, entries: list[TimelineEntry]) -> None:
        """
        Load timeline from a list of entries, optimizing for compressed context.

        This method implements the loading optimization:
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
