"""
Context Auto-Compaction Service for Template Fine-Tuning Chat

Intelligently compacts conversation history by summarizing older messages
while preserving critical context, user instructions, and template content.
Inspired by Claude Code's context management approach.

The compacted summary is stored in the metadata field of the first preserved
message, not as a separate message. When building the LLM prompt, handlers
inject this metadata as a <prior_conversation_summary> block.
"""

import hashlib
import logging
import time
from dataclasses import dataclass
from enum import StrEnum

from dana.lang.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource as LLMResource
from dana.lang.common.types import BaseRequest
from dana.lang.common.utils.misc import Misc
from dana.lang.common.utils.token_management import TokenManagement
from dana.studio.api.core.schemas import MessageData, SenderRole

logger = logging.getLogger(__name__)


class MessagePriority(StrEnum):
    """Priority levels for message preservation during compaction."""

    CRITICAL = "critical"  # System messages, must never compact
    HIGH = "high"  # Template content, user instructions with special markers
    MEDIUM = "medium"  # Recent messages, require_user messages
    LOW = "low"  # Tool results, intermediate thinking


@dataclass
class CompactionConfig:
    """Configuration for context compaction behavior."""

    # Token thresholds
    target_token_limit: int = 80000  # Target after compaction
    compaction_trigger: int = 100000  # When to trigger compaction
    safety_margin: int = 10000  # Buffer for response generation

    # Message preservation
    preserve_recent_count: int = 6  # Always keep last N messages
    preserve_system_messages: bool = True  # Never compact system messages

    # Summarization settings
    summary_model: str | None = None  # Use default LLM if None
    max_summary_tokens: int = 2000  # Max tokens per summary block

    # Caching
    enable_cache: bool = True  # Cache summaries by content hash
    cache_ttl_seconds: int = 3600  # 1 hour cache TTL


@dataclass
class CompactionResult:
    """Result of a compaction operation."""

    original_token_count: int
    compacted_token_count: int
    messages_compacted: int
    messages_preserved: int
    summary_created: bool
    compacted_conversation: list[MessageData]


# Prompt for generating conversation summaries
SUMMARY_PROMPT = """You are a conversation summarizer for an interview template editing system.

Summarize the following conversation segment, focusing on preserving context needed for continuing the conversation.

## CRITICAL: Preserve These Exactly
1. **User Instructions**: Any instructions the user gave about what to keep, preserve, or not change
   - Look for phrases like "keep", "always", "remember", "don't change", "preserve", "unchanged"
   - Quote these instructions exactly if possible

2. **Active Constraints**: Ongoing rules the user established
   - What sections/topics should NOT be modified
   - What style or format to maintain
   - Any "always do X" or "never do Y" rules

3. **Current State**: What has been done so far
   - Which topics/sections were modified
   - What the template looks like now (high-level)

4. **Actions Taken**: Brief summary of modifications made
   - Questions added, removed, or refined
   - Sections viewed or edited

## Conversation to Summarize
{conversation_content}

## Output Format
Provide a structured summary in markdown (max 400 words):

### User Instructions
[Bullet points of user instructions, especially preservation requests]

### Actions Taken
[Brief bullet points of what was done]

### Current State
[1-2 sentences about current template state]

### Active Constraints
[Any ongoing rules or constraints]

IMPORTANT: If the user said something like "keep section X unchanged" or "don't modify Y",
this MUST appear in the summary. These instructions are critical for continuing the conversation correctly.
"""


class ContextAutoCompactor:
    """
    Service for intelligently compacting conversation context.

    Approach:
    1. Split conversation into older messages and preserved recent messages
    2. Generate a summary of older messages using LLM
    3. Attach summary to metadata of first preserved message
    4. Return only preserved messages (with summary in metadata)

    The handler is responsible for injecting the metadata summary into the
    LLM prompt when building messages.
    """

    def __init__(
        self,
        llm: LLMResource | None = None,
        config: CompactionConfig | None = None,
    ):
        self.llm = llm or LLMResource()
        self.config = config or CompactionConfig()
        self._summary_cache: dict[str, tuple[str, float]] = {}  # hash -> (summary, timestamp)

    async def compact_if_needed(
        self,
        conversation: list[MessageData],
        model: str | None = None,
        _depth: int = 0,
    ) -> CompactionResult:
        """
        Main entry point. Compacts conversation if token threshold exceeded.

        Args:
            conversation: List of MessageData messages
            model: Target model for token limit calculation (optional)
            _depth: Internal recursion depth tracker

        Returns:
            CompactionResult with compacted conversation
        """
        MAX_COMPACTION_DEPTH = 3

        if _depth >= MAX_COMPACTION_DEPTH:
            logger.warning("Max compaction depth reached, using aggressive truncation")
            return self._aggressive_truncation_fallback(conversation)

        # Handle empty or minimal conversations
        if len(conversation) <= self.config.preserve_recent_count:
            token_count = self.estimate_conversation_tokens(conversation)
            return CompactionResult(
                original_token_count=token_count,
                compacted_token_count=token_count,
                messages_compacted=0,
                messages_preserved=len(conversation),
                summary_created=False,
                compacted_conversation=conversation,
            )

        # Estimate current token count
        original_tokens = self.estimate_conversation_tokens(conversation)

        # Check if compaction is needed
        if original_tokens < self.config.compaction_trigger:
            return CompactionResult(
                original_token_count=original_tokens,
                compacted_token_count=original_tokens,
                messages_compacted=0,
                messages_preserved=len(conversation),
                summary_created=False,
                compacted_conversation=conversation,
            )

        logger.info(f"Compaction triggered: {original_tokens} tokens > {self.config.compaction_trigger} threshold")

        # Split conversation into older and preserved recent
        preserve_count = self.config.preserve_recent_count
        preserved_recent = conversation[-preserve_count:]
        older_messages = conversation[:-preserve_count]

        if not older_messages:
            # Nothing to compact
            return CompactionResult(
                original_token_count=original_tokens,
                compacted_token_count=original_tokens,
                messages_compacted=0,
                messages_preserved=len(conversation),
                summary_created=False,
                compacted_conversation=conversation,
            )

        # Check cache for existing summary
        content_hash = self._get_content_hash(older_messages)
        cached_summary = self._get_cached_summary(content_hash)

        if cached_summary:
            logger.debug("Using cached summary for conversation compaction")
            summary = cached_summary
        else:
            # Generate summary of older messages
            try:
                summary = await self.generate_context_summary(older_messages)
                self._cache_summary(content_hash, summary)
            except Exception as e:
                logger.warning(f"Summarization failed: {e}, falling back to key extraction")
                summary = self._extract_key_information_fallback(older_messages)

        # Attach summary to first preserved message
        compacted = self.attach_summary_to_first_message(preserved_recent, summary)

        # Calculate new token count
        compacted_tokens = self.estimate_conversation_tokens(compacted)

        logger.info(
            f"Compaction complete: {original_tokens} -> {compacted_tokens} tokens "
            f"({len(older_messages)} messages summarized, {len(compacted)} preserved)"
        )

        # Check if we're still over the target
        if compacted_tokens > self.config.target_token_limit:
            logger.info(
                f"Still over target ({compacted_tokens} > {self.config.target_token_limit}), " "retrying with reduced preserve count"
            )
            # Reduce preserve count and retry
            reduced_config = CompactionConfig(
                **{
                    **self.config.__dict__,
                    "preserve_recent_count": max(2, self.config.preserve_recent_count - 2),
                }
            )
            reduced_compactor = ContextAutoCompactor(llm=self.llm, config=reduced_config)
            return await reduced_compactor.compact_if_needed(compacted, model, _depth=_depth + 1)

        return CompactionResult(
            original_token_count=original_tokens,
            compacted_token_count=compacted_tokens,
            messages_compacted=len(older_messages),
            messages_preserved=len(compacted),
            summary_created=True,
            compacted_conversation=compacted,
        )

    def estimate_conversation_tokens(self, conversation: list[MessageData]) -> int:
        """Estimate total token count for conversation."""
        total = 0
        for message in conversation:
            msg_dict = {"role": message.role, "content": message.content}
            total += TokenManagement.estimate_message_tokens(msg_dict)

            # Account for metadata if it contains compacted context
            if message.metadata.get("compacted_context"):
                total += TokenManagement.estimate_tokens(message.metadata["compacted_context"])

        return total

    async def generate_context_summary(self, older_messages: list[MessageData]) -> str:
        """
        Generate structured summary for older messages using LLM.

        Args:
            older_messages: List of messages to summarize

        Returns:
            Structured summary string
        """
        # Build conversation content for the prompt
        conversation_lines = []
        for i, msg in enumerate(older_messages):
            role = msg.role.upper() if isinstance(msg.role, str) else str(msg.role).upper()
            content = msg.content

            # Truncate very long tool results
            if msg.treat_as_tool and len(content) > 500:
                content = content[:500] + "... [truncated]"

            conversation_lines.append(f"[{i + 1}] {role}: {content}")

        conversation_content = "\n\n".join(conversation_lines)

        # Build the prompt
        prompt = SUMMARY_PROMPT.format(conversation_content=conversation_content)

        # Call LLM
        llm_request = BaseRequest(
            arguments={
                "messages": [
                    {"role": "system", "content": "You are a precise conversation summarizer."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": self.config.max_summary_tokens,
            }
        )

        response = await self.llm.query(llm_request)
        summary = Misc.get_response_content(response).strip()

        return summary

    def attach_summary_to_first_message(
        self,
        preserved: list[MessageData],
        summary: str,
    ) -> list[MessageData]:
        """
        Attach compacted context summary to the first preserved message's metadata.

        Args:
            preserved: List of preserved messages
            summary: The generated summary

        Returns:
            New list with summary attached to first message's metadata
        """
        if not preserved:
            return preserved

        # Create a copy of the list with updated first message
        result = []
        for i, msg in enumerate(preserved):
            if i == 0:
                # Create new MessageData with updated metadata
                new_metadata = {**msg.metadata, "compacted_context": summary}
                new_msg = MessageData(
                    role=msg.role,
                    content=msg.content,
                    require_user=msg.require_user,
                    treat_as_tool=msg.treat_as_tool,
                    metadata=new_metadata,
                )
                result.append(new_msg)
            else:
                result.append(msg)

        return result

    def _get_content_hash(self, messages: list[MessageData]) -> str:
        """Generate hash for message content for caching."""
        content = "".join(f"{m.role}:{m.content}" for m in messages)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_cached_summary(self, content_hash: str) -> str | None:
        """Retrieve cached summary if valid."""
        if not self.config.enable_cache:
            return None

        self._cleanup_expired_cache()

        if content_hash in self._summary_cache:
            summary, timestamp = self._summary_cache[content_hash]
            if time.time() - timestamp < self.config.cache_ttl_seconds:
                return summary
            else:
                del self._summary_cache[content_hash]

        return None

    def _cache_summary(self, content_hash: str, summary: str) -> None:
        """Cache a generated summary."""
        if self.config.enable_cache:
            self._summary_cache[content_hash] = (summary, time.time())

    def _cleanup_expired_cache(self) -> None:
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._summary_cache.items() if current_time - timestamp > self.config.cache_ttl_seconds
        ]
        for key in expired_keys:
            del self._summary_cache[key]

    def _extract_key_information_fallback(self, messages: list[MessageData]) -> str:
        """
        Non-LLM fallback for summarization.
        Extracts key patterns from messages when LLM call fails.
        """
        user_instructions = []
        actions = []

        instruction_markers = ["keep", "always", "remember", "don't", "preserve", "unchanged", "never"]

        for msg in messages:
            content_lower = msg.content.lower()

            # Extract user instructions
            if msg.role == SenderRole.USER or msg.role == "user":
                if any(marker in content_lower for marker in instruction_markers):
                    # Extract the instruction (first 200 chars)
                    user_instructions.append(msg.content[:200])

            # Extract tool actions
            if msg.treat_as_tool:
                if "<view_template>" in msg.content:
                    actions.append("Template was viewed")
                if "<replace_in_template>" in msg.content:
                    actions.append("Template was modified")
                if "<ask_question>" in msg.content:
                    actions.append("Question was asked")

        # Build fallback summary
        summary_parts = ["## Prior Conversation Summary (Fallback - LLM Unavailable)"]

        if user_instructions:
            summary_parts.append("\n### User Instructions")
            for instr in user_instructions[:5]:  # Limit to 5
                summary_parts.append(f"- {instr}")

        if actions:
            summary_parts.append("\n### Actions Taken")
            # Deduplicate actions
            unique_actions = list(dict.fromkeys(actions))
            for action in unique_actions[:5]:
                summary_parts.append(f"- {action}")

        if not user_instructions and not actions:
            summary_parts.append("\n- Previous conversation context (details unavailable)")

        return "\n".join(summary_parts)

    def _aggressive_truncation_fallback(self, conversation: list[MessageData]) -> CompactionResult:
        """
        Fallback when max compaction depth is reached.
        Simply keeps the most recent messages.
        """
        preserve_count = max(2, self.config.preserve_recent_count // 2)
        truncated = conversation[-preserve_count:]

        original_tokens = self.estimate_conversation_tokens(conversation)
        truncated_tokens = self.estimate_conversation_tokens(truncated)

        logger.warning(
            f"Aggressive truncation: {len(conversation)} -> {len(truncated)} messages " f"({original_tokens} -> {truncated_tokens} tokens)"
        )

        return CompactionResult(
            original_token_count=original_tokens,
            compacted_token_count=truncated_tokens,
            messages_compacted=len(conversation) - len(truncated),
            messages_preserved=len(truncated),
            summary_created=False,
            compacted_conversation=truncated,
        )


def inject_compacted_context_to_content(message: MessageData) -> str:
    """
    Helper function for handlers to inject compacted context into message content.

    If the message has compacted_context in metadata, prepends it to the content
    wrapped in <prior_conversation_summary> tags.

    Args:
        message: The MessageData to process

    Returns:
        Content string with compacted context prepended if available
    """
    compacted_context = message.metadata.get("compacted_context")
    if compacted_context:
        return f"<prior_conversation_summary>\n" f"{compacted_context}\n" f"</prior_conversation_summary>\n\n" f"{message.content}"
    return message.content
