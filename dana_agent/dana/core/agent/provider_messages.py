"""
Provider message conversion mixin for CompressedTimeline.

Provides ProviderMessagesMixin with methods to convert native messages
to provider-specific formats: to_llm_messages, to_openai_messages,
to_anthropic_messages, and supporting token-limit helpers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from structlog import get_logger

from dana.common.llm.types import LLMMessage


if TYPE_CHECKING:
    from dana.core.agent.compressed_timeline import CompressedTimeline

logger = get_logger()

# Type aliases for provider-specific message formats
OpenAIMessage = dict[str, Any]
AnthropicMessage = dict[str, Any]


class ProviderMessagesMixin:
    """
    Mixin providing LLM provider message conversion for CompressedTimeline.

    Expects the following attributes on self (provided by CompressedTimeline):
        _native_messages: list[NativeMessage]
        max_context_tokens: int
        get_compressed_context: callable
    """

    def to_llm_messages(
        self: CompressedTimeline,
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
                isinstance(msg.content, str)
                and (msg.content.startswith("[Previous context summary]") or msg.content.startswith("[SUMMARY]"))
                for msg in messages
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

    def _apply_token_limit_to_messages(self: CompressedTimeline, messages: list[LLMMessage], max_tokens: int) -> list[LLMMessage]:
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

    def to_openai_messages(
        self: CompressedTimeline,
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
        self: CompressedTimeline,
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
