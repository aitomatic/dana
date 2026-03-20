"""
Token-limiting helpers for CompressedTimeline message windowing.

Provides standalone functions to estimate token counts and apply sliding-window
token limits to lists of LLMMessage objects, keeping tool_call/tool_result pairs
together as atomic units.
"""

from __future__ import annotations

from dana.common.llm.types import LLMMessage


def estimate_messages_tokens(messages: list[LLMMessage]) -> int:
    """
    Estimate token count for a list of LLMMessage objects.

    Uses a character-based heuristic (4 chars per token).

    Args:
        messages: List of LLMMessage objects

    Returns:
        Estimated token count
    """
    total = 0
    for msg in messages:
        # Rough estimation: 4 characters per token
        content = msg.content
        total += len(content) // 4 if isinstance(content, str) else len(str(content)) // 4
        # Add tokens for tool_calls if present
        if msg.tool_calls:
            for tc in msg.tool_calls:
                if isinstance(tc, dict):
                    total += len(str(tc)) // 4
                else:
                    total += len(str(tc)) // 4
    return total


def apply_token_limit_to_messages(messages: list[LLMMessage], max_tokens: int) -> list[LLMMessage]:
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
    system_tokens = sum(estimate_messages_tokens(g) for g in system_groups)
    available_tokens = max_tokens - system_tokens

    # Build result from most recent non-system groups, respecting token limit
    result_groups: list[list[LLMMessage]] = []
    current_tokens = 0

    for group in reversed(non_system_groups):
        group_tokens = estimate_messages_tokens(group)

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
