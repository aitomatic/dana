"""
Protocol interfaces and shared dataclasses for the dana_agent runtime.

Defines the structural contracts (Protocols) for the major components of
AgentRuntime, enabling loose coupling and dependency injection. All protocols
are @runtime_checkable so isinstance() checks work at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable


if TYPE_CHECKING:
    from dana.core.agent.timeline import Timeline

from dana.common.llm.types import LLMMessage, LLMResponse


# ---------------------------------------------------------------------------
# Shared dataclasses (moved from base.py)
# ---------------------------------------------------------------------------


@dataclass
class TodoItem:
    content: str
    status: str  # "pending", "in_progress", "completed"


@dataclass
class ParsedResponse:
    done: bool | None
    reasoning: str | None
    response: str | None
    tool_calls: list[dict[str, Any]]
    todo_list: list[TodoItem] | None = None


# ---------------------------------------------------------------------------
# Approval types (defined before ApprovalProtocol so it can reference them)
# ---------------------------------------------------------------------------


@dataclass
class ApprovalResult:
    approved: bool
    reason: str | None = None


# ---------------------------------------------------------------------------
# Stream event types
# ---------------------------------------------------------------------------


class StreamEventType(Enum):
    THINKING = "thinking"
    TEXT_DELTA = "text_delta"
    TOOL_CALL_START = "tool_call_start"
    TOOL_RESULT = "tool_result"
    DONE = "done"
    ERROR = "error"


@dataclass
class StreamEvent:
    event_type: StreamEventType
    data: Any
    iteration: int


# ---------------------------------------------------------------------------
# Protocol interfaces
# ---------------------------------------------------------------------------


@runtime_checkable
class PromptBuilderProtocol(Protocol):
    """Builds the list of LLM messages for a given agent iteration."""

    def build_prompt(
        self,
        agent: Any,
        timeline: Timeline,
        learned_context: str | None = None,
    ) -> list[LLMMessage]: ...


@runtime_checkable
class LLMCallerProtocol(Protocol):
    """Calls an LLM (sync and async variants)."""

    def call_llm(self, messages: list[LLMMessage]) -> LLMResponse: ...

    async def call_llm_async(self, messages: list[LLMMessage]) -> LLMResponse: ...


@runtime_checkable
class ResponseParserProtocol(Protocol):
    """Parses a raw LLM response into a structured ParsedResponse."""

    def parse_response(self, response: LLMResponse) -> ParsedResponse: ...

    def validate_done_output(
        self,
        done: bool | None,
        has_tool_calls: bool,
        has_response: bool,
    ) -> str: ...

    def build_output_format_correction(self) -> LLMMessage: ...


@runtime_checkable
class ToolExecutorProtocol(Protocol):
    """Executes tool calls and returns their results (sync and async)."""

    def execute_tools(self, agent: Any, tool_calls: list[dict], parallel: bool = False) -> list[dict]: ...

    async def execute_tools_async(self, agent: Any, tool_calls: list[dict]) -> list[dict]: ...


@runtime_checkable
class ToolHookProtocol(Protocol):
    """Lifecycle hooks called around individual tool executions."""

    async def before_tool_call(self, agent: Any, tool_call: dict) -> dict | None: ...

    async def after_tool_call(self, agent: Any, tool_call: dict, result: dict) -> dict: ...


@runtime_checkable
class ApprovalProtocol(Protocol):
    """Requests human (or automated) approval before executing tool calls."""

    async def request_approval(
        self,
        agent: Any,
        tool_calls: list[dict],
    ) -> ApprovalResult: ...
