"""
LLM Types and Base Classes

Core types and abstract base classes for LLM functionality.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class LLMError(Exception):
    """Base exception for LLM operations."""

    pass


class ProviderError(LLMError):
    """Exception raised when provider operations fail."""

    pass


class ConfigurationError(LLMError):
    """Exception raised for configuration issues."""

    pass


@dataclass
class LLMMessage:
    """A single message in a conversation."""

    content: str
    role: str  # "system", "user", "assistant", "tool"
    cache_control: dict | None = None  # For Anthropic prompt caching
    tool_calls: list | None = None  # For assistant messages with native tool calls
    tool_call_id: str | None = None  # For tool result messages (role="tool")


@dataclass
class SystemLLMMessage(LLMMessage):
    """A system message in a conversation."""

    content: str
    role: str = "system"  # Hard-coded role
    cache_control: dict | None = None  # For Anthropic prompt caching


@dataclass
class UserLLMMessage(LLMMessage):
    """A user message in a conversation."""

    content: str
    role: str = "user"  # Hard-coded role


@dataclass
class AssistantLLMMessage(LLMMessage):
    """An assistant message in a conversation."""

    content: str
    role: str = "assistant"  # Hard-coded role


@dataclass
class ToolLLMMessage(LLMMessage):
    """A tool result message for native OpenAI tool calling."""

    content: str
    tool_call_id: str
    role: str = "tool"  # Hard-coded role


@dataclass
class LLMResponse:
    """Response from an LLM call."""

    content: str
    model: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None
    tool_calls: list | None = None  # For function calling support
    reasoning_content: str | None = None  # From providers that expose thinking (DeepSeek, future Claude extended)
    reasoning_tokens: int | None = None  # Token count from OpenAI thinking models


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    def supports_native_tools(self) -> bool:
        """Whether this provider supports native function/tool calling.

        Override in providers that support OpenAI-compatible tool calling.
        """
        return False

    @abstractmethod
    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Send messages to the LLM and get a response."""
        pass
