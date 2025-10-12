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
    role: str  # "system", "user", "assistant"


@dataclass
class SystemLLMMessage(LLMMessage):
    """A system message in a conversation."""

    content: str
    role: str = "system"  # Hard-coded role


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
class LLMResponse:
    """Response from an LLM call."""

    content: str
    model: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None
    tool_calls: list | None = None  # For function calling support


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        """Send messages to the LLM and get a response."""
        pass
