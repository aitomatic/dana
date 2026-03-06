"""
Compression engine mixin for CompressedTimeline.

Provides CompressionMixin with all compression-related methods:
needs_compression, get_entries_to_keep_and_compress, compress, compress_async,
_apply_compression, build_compression_prompt, etc.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from structlog import get_logger

from dana.core.timeline.native_message import (
    COMPRESSED_CONTEXT_KEY,
    COMPRESSED_ENTRIES_COUNT_KEY,
    COMPRESSION_TIMESTAMP_KEY,
    NativeMessage,
)
from dana.core.timeline.timeline import TimelineEntry, TimelineEntryType


if TYPE_CHECKING:
    from dana.core.timeline.compressed_timeline import CompressedTimeline

logger = get_logger()


class CompressionMixin:
    """
    Mixin providing LLM-based compression logic for CompressedTimeline.

    Expects the following attributes on self (provided by CompressedTimeline):
        _compressed_config: CompressedTimelineConfig
        _native_messages: list[NativeMessage]
        timeline: list[TimelineEntry]
        _llm_call_fn: Callable | None
        _llm_call_async_fn: Callable | None
        cutoff_when_token_reach: int
        max_recent_entries_to_keep: int
    """

    # ------------------------------------------------------------------
    # Token estimation helpers
    # ------------------------------------------------------------------

    def _estimate_entry_tokens(self: CompressedTimeline, entry: TimelineEntry) -> int:
        """
        Estimate token count for a single entry.

        Args:
            entry: TimelineEntry to estimate

        Returns:
            Estimated token count
        """
        # Rough estimation: 4 characters per token
        content = entry.content
        if isinstance(content, list):
            # Multimodal content: estimate text parts only
            total = 0
            for block in content:
                if isinstance(block, dict) and "text" in block:
                    total += len(block["text"])
            return int(total / 4)
        return int(len(str(content)) / 4)

    # ------------------------------------------------------------------
    # Needs compression check
    # ------------------------------------------------------------------

    def needs_compression(self: CompressedTimeline) -> bool:
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

    # ------------------------------------------------------------------
    # Partition logic: which messages/entries to keep vs. compress
    # ------------------------------------------------------------------

    def get_entries_to_keep_and_compress(
        self: CompressedTimeline,
    ) -> tuple[list[TimelineEntry], list[TimelineEntry]]:
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

    def _ensure_tool_pair_integrity(self: CompressedTimeline, entries: list[TimelineEntry]) -> list[TimelineEntry]:
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

    def get_native_messages_to_keep_and_compress(
        self: CompressedTimeline,
    ) -> tuple[list[NativeMessage], list[NativeMessage]]:
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

    def _ensure_native_message_tool_pair_integrity(self: CompressedTimeline, messages: list[NativeMessage]) -> list[NativeMessage]:
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

    # ------------------------------------------------------------------
    # Compression prompt construction
    # ------------------------------------------------------------------

    def build_compression_prompt(self: CompressedTimeline) -> str | None:
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

    def _format_entries_for_compression(self: CompressedTimeline, entries: list[TimelineEntry]) -> str:
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
            if isinstance(content, list):
                # Multimodal content: extract text parts for compression
                text_parts = [b.get("text", "") for b in content if isinstance(b, dict) and "text" in b]
                content = " ".join(text_parts) if text_parts else "[multimodal content]"
            if len(content) > 1000:
                content = content[:1000] + "... [truncated]"

            role = role_map.get(entry.entry_type, entry.entry_type.value)
            formatted_parts.append(f"[{role}] {content}")

        return "\n\n".join(formatted_parts)

    # ------------------------------------------------------------------
    # Core compress / compress_async methods
    # ------------------------------------------------------------------

    def compress(self: CompressedTimeline) -> int:
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

    async def compress_async(self: CompressedTimeline) -> int:
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

    # ------------------------------------------------------------------
    # Apply compression & extract summary
    # ------------------------------------------------------------------

    def _apply_compression(
        self: CompressedTimeline,
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

    # ------------------------------------------------------------------
    # Public compressed context accessors
    # ------------------------------------------------------------------

    def get_compressed_context(self: CompressedTimeline) -> str | None:
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

    def has_compressed_context(self: CompressedTimeline) -> bool:
        """
        Check if timeline has compressed context.

        Returns:
            True if compressed context exists in any entry's metadata
        """
        return self.get_compressed_context() is not None

    def compress_old_entries(self: CompressedTimeline, summary: str) -> int:
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

    def get_entries_for_compression(self: CompressedTimeline) -> list[TimelineEntry]:
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
