"""Token management utilities for LLM interactions.

This module provides utilities for estimating token counts, managing context
windows, and preventing token limit overflows.
"""

import re
from typing import Any

# Default token limits for different models (conservative estimates)
DEFAULT_MODEL_TOKENS = {
    # OpenAI models
    "openai:gpt-3.5-turbo": 4096,
    "openai:gpt-3.5-turbo-1106": 16384,
    "openai:gpt-4": 8192,
    "openai:gpt-4-32k": 32768,
    "openai:gpt-4-turbo": 128000,
    "openai:gpt-4o": 128000,
    "openai:gpt-4o-mini": 128000,
    # Anthropic models
    "anthropic:claude-2": 100000,
    "anthropic:claude-2.1": 200000,
    "anthropic:claude-3-opus": 200000,
    "anthropic:claude-3-sonnet": 200000,
    "anthropic:claude-3-haiku": 200000,
    # Other providers (add as needed)
    "groq:llama3-70b": 8192,
    "groq:llama3-8b": 8192,
    "groq:mixtral-8x7b": 32768,
    # Default fallbacks by provider
    "openai": 4096,  # Conservative default
    "anthropic": 100000,
    "cohere": 4096,
    "groq": 8192,
    "default": 4096,  # Global fallback
}


class TokenManagement:
    """Utilities for token estimation and context window management."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate the number of tokens in a string.

        This is a simple approximation that works fairly well for English text.
        For production use with specific models, consider using model-specific
        tokenizers like tiktoken for OpenAI models.

        Args:
            text: The text to estimate tokens for

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        # Split into words, treating punctuation as separate tokens
        words = re.findall(r"\w+|[^\w\s]", text)

        # Estimate tokens based on GPT-like tokenizers:
        # - Words are typically 1-2 tokens depending on length and commonality
        # - Punctuation and special characters are usually 1 token each
        # - This rough estimate gives ~4 characters per token
        char_count = len(text)
        return max(len(words), char_count // 4)

    @staticmethod
    def estimate_message_tokens(message: dict[str, Any]) -> int:
        """Estimate tokens in a message.

        Args:
            message: A message dictionary with 'role' and 'content'

        Returns:
            Estimated token count
        """
        # Base tokens for message format (role, metadata)
        base_tokens = 4

        # Add content tokens
        content = message.get("content", "")
        if isinstance(content, str):
            base_tokens += TokenManagement.estimate_tokens(content)
        elif hasattr(content, "__str__"):
            # Handle objects that can be converted to string (like CallToolResult)
            base_tokens += TokenManagement.estimate_tokens(str(content))
        else:
            # For other types, use a conservative estimate
            base_tokens += 10

        # Add tool calls if present
        tool_calls = message.get("tool_calls", [])
        if tool_calls and isinstance(tool_calls, list):
            for call in tool_calls:
                # Function name and arguments
                if isinstance(call, dict):
                    func = call.get("function", {})
                    if isinstance(func, dict):
                        name = func.get("name", "")
                        args = func.get("arguments", "{}")
                        base_tokens += TokenManagement.estimate_tokens(name) + TokenManagement.estimate_tokens(args)

        return base_tokens

    @staticmethod
    def get_model_token_limit(model: str | None = None) -> int:
        """Get the token limit for a specific model.

        Args:
            model: The model identifier (provider:model_name)

        Returns:
            The token limit for the model
        """
        if not model:
            return DEFAULT_MODEL_TOKENS["default"]

        # Check for exact match
        if model in DEFAULT_MODEL_TOKENS:
            return DEFAULT_MODEL_TOKENS[model]

        # Check provider fallback
        provider = model.split(":", 1)[0] if ":" in model else "default"
        if provider in DEFAULT_MODEL_TOKENS:
            return DEFAULT_MODEL_TOKENS[provider]

        # Use global default
        return DEFAULT_MODEL_TOKENS["default"]

    @staticmethod
    def enforce_context_window(
        messages: list[dict[str, Any]],
        model: str | None = None,
        max_tokens: int | None = None,
        preserve_system_messages: bool = True,
        preserve_latest_messages: int = 4,
        safety_margin: int = 200,
    ) -> list[dict[str, Any]]:
        """Ensure messages fit within a model's context window.

        This method will:
        1. Preserve all system messages if requested
        2. Preserve the most recent N messages
        3. Drop older messages if needed to fit within the token limit

        Args:
            messages: The message list to enforce limits on
            model: The model identifier (for token limit detection)
            max_tokens: Override the model's default token limit
            preserve_system_messages: Whether to always keep system messages
            preserve_latest_messages: Number of recent messages to preserve
            safety_margin: Token buffer to leave for the response

        Returns:
            A potentially truncated message list
        """
        if not messages:
            return []

        # Determine token limit
        if max_tokens:
            token_limit = max_tokens
        else:
            token_limit = TokenManagement.get_model_token_limit(model)

        # Account for safety margin
        token_limit -= safety_margin

        # Initialize preserved messages
        preserved_messages = []

        # Always preserve system messages if requested
        if preserve_system_messages:
            system_messages = [m for m in messages if m.get("role") == "system"]
            preserved_messages.extend(system_messages)

            # Count tokens used by system messages
            system_tokens = sum(TokenManagement.estimate_message_tokens(m) for m in system_messages)
            token_limit -= system_tokens

        # Get non-system messages
        non_system_messages = [m for m in messages if m.get("role") != "system" or not preserve_system_messages]

        # Always preserve the most recent messages up to the limit
        recent_messages = non_system_messages[-preserve_latest_messages:]
        remaining_messages = non_system_messages[:-preserve_latest_messages] if len(non_system_messages) > preserve_latest_messages else []

        # Count tokens for recent messages (these are always kept if possible)
        recent_tokens = sum(TokenManagement.estimate_message_tokens(m) for m in recent_messages)

        # If just the recent messages exceed the limit, we need to drop some
        if recent_tokens > token_limit:
            # Start dropping from the oldest recent messages
            while recent_messages and recent_tokens > token_limit:
                dropped_message = recent_messages.pop(0)
                recent_tokens -= TokenManagement.estimate_message_tokens(dropped_message)

            # Add remaining recent messages to preserved list
            preserved_messages.extend(recent_messages)
            return preserved_messages

        # We have room for some earlier messages
        token_limit -= recent_tokens

        # Add as many remaining messages as will fit, starting from most recent
        remaining_messages.reverse()  # Start with most recent
        for message in remaining_messages:
            message_tokens = TokenManagement.estimate_message_tokens(message)
            if message_tokens <= token_limit:
                preserved_messages.append(message)
                token_limit -= message_tokens
            else:
                # This message would exceed the limit, skip it
                continue

        # Add the recent messages
        preserved_messages.extend(recent_messages)

        # Sort preserved messages to maintain original order
        preserved_messages.sort(key=lambda m: messages.index(m))

        return preserved_messages
