"""
LLM Types and Base Classes

Core types, Protocol definition, and base class for LLM providers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    from dana.common.schemas.tool_call import MethodSignature


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

    content: str | list[dict]
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

    content: str | list[dict]
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


@dataclass
class LLMStreamChunk:
    """A single chunk from a streaming LLM response."""

    type: str  # "text_delta", "tool_use", "thinking"
    content: str = ""
    tool_call: dict | None = None  # {"id": str, "name": str, "input": dict}


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """Structural typing protocol for LLM providers.

    Third-party providers can satisfy this protocol without inheriting from LLMProvider.
    Use isinstance(x, LLMProviderProtocol) for runtime checks.
    """

    @property
    def supports_native_tools(self) -> bool: ...

    def prepare_messages(self, messages: list[LLMMessage]) -> tuple[Any, list[dict]]:
        """Convert LLMMessage[] to provider wire format.

        Returns: (system_param, messages_list) — system_param is provider-specific.
        """
        ...

    def prepare_tools(self, tools: list[MethodSignature]) -> list[dict]:
        """Convert MethodSignature[] to provider-specific tool schema."""
        ...

    async def chat(self, messages: list[LLMMessage], tools: list | None = None, **kwargs) -> LLMResponse: ...

    async def stream(self, messages: list[LLMMessage], tools: list | None = None, **kwargs): ...


class LLMProvider:
    """Base class for LLM providers. Satisfies LLMProviderProtocol.

    Provides default implementations for prepare_messages() and prepare_tools().
    Subclasses override chat() and optionally the prepare methods.
    """

    # Default timeout in seconds for LLM API calls (2 minutes).
    # Prevents long-running calls (e.g. timeline compression) from blocking the agent loop.
    DEFAULT_TIMEOUT_SECONDS = 120

    @property
    def supports_native_tools(self) -> bool:
        """Whether this provider supports native function/tool calling."""
        return False

    def prepare_messages(self, messages: list[LLMMessage]) -> tuple[Any, list[dict]]:
        """Default: extract system message, convert rest to basic dicts."""
        system = None
        converted = []
        for msg in messages:
            # Guard against None content — APIs reject null content
            safe_content = msg.content if msg.content is not None else ""
            if msg.role == "system":
                system = safe_content
            elif msg.role == "tool":
                converted.append(
                    {
                        "role": "tool",
                        "tool_call_id": msg.tool_call_id,
                        "content": safe_content,
                    }
                )
            elif msg.role == "assistant" and msg.tool_calls:
                formatted_tool_calls = []
                for tc in msg.tool_calls:
                    tc_id = tc.get("tool_call_id") or tc.get("id", "")
                    tc_name = tc.get("function") or tc.get("name", "")
                    formatted_tool_calls.append(
                        {
                            "id": tc_id,
                            "type": "function",
                            "function": {
                                "name": tc_name,
                                "arguments": str(tc.get("arguments", {})),
                            },
                        }
                    )
                converted.append(
                    {
                        "role": "assistant",
                        "content": safe_content,
                        "tool_calls": formatted_tool_calls,
                    }
                )
            else:
                converted.append({"role": msg.role, "content": safe_content})
        return system, converted

    def prepare_tools(self, tools: list[MethodSignature]) -> list[dict]:
        """Default: convert MethodSignature[] to OpenAI-compatible tool schema format."""
        result = []
        for sig in tools:
            params: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
            for p in sig.parameters:
                prop: dict[str, Any] = {"type": p.type if hasattr(p, "type") else "string"}
                if p.description:
                    prop["description"] = p.description
                params["properties"][p.name] = prop
                if not p.has_default:
                    params["required"].append(p.name)
            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": sig.name,
                        "description": sig.description,
                        "parameters": params,
                    },
                }
            )
        return result

    async def chat(self, messages: list[LLMMessage], tools: list | None = None, **kwargs) -> LLMResponse:
        """Send messages to the LLM and get a response."""
        raise NotImplementedError

    async def stream(self, messages: list[LLMMessage], tools: list | None = None, **kwargs):
        """Stream LLMStreamChunk from the LLM."""
        raise NotImplementedError
