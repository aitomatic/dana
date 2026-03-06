"""
Native message types for provider-agnostic LLM conversation representation.

Provides NativeMessageRole, NativeToolCall, NativeMessage dataclasses and
the metadata key constants used for compressed context storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from dana.common.llm.types import LLMMessage


# Type alias for native message roles
NativeMessageRole = Literal["user", "assistant", "system", "tool"]

# Metadata keys for compressed context storage
COMPRESSED_CONTEXT_KEY = "compressed_context"
COMPRESSION_TIMESTAMP_KEY = "compression_timestamp"
COMPRESSED_ENTRIES_COUNT_KEY = "compressed_entries_count"


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
