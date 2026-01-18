from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from dana.common.llm.types import LLMMessage


@dataclass
class ParsedResponse:
    done: bool | None
    reasoning: str | None
    response: str | None
    tool_calls: list[dict[str, Any]]


class AgentRuntime(ABC):
    @abstractmethod
    def build_prompt(self, agent, timeline, learned_context: str | None = None) -> list[LLMMessage]:
        raise NotImplementedError

    @abstractmethod
    def call_llm(self, messages: list[LLMMessage]) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse_response(self, raw: str) -> ParsedResponse:
        raise NotImplementedError

    @abstractmethod
    def execute_tools(self, agent, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        raise NotImplementedError

    def validate_done_output(self, done: bool | None, has_tool_calls: bool, has_response: bool) -> str:
        if done is None:
            return "retry"
        if done and has_tool_calls:
            return "retry"
        if not done and has_response:
            return "retry"
        if not done and not has_tool_calls:
            return "retry"
        if done and not has_response:
            return "retry"
        return "exit" if done else "continue"

    def build_output_format_correction(self) -> LLMMessage:
        return LLMMessage(
            role="user",
            content=(
                "Invalid format. Reply with ONLY valid JSON:\n"
                '{"done": false, "reasoning": "...", "response": null, "tool_calls": [{"name": "...", "parameters": {...}}]}\n'
                "OR\n"
                '{"done": true, "reasoning": "...", "response": "your answer", "tool_calls": []}\n'
                "Rules: done=false requires tool_calls. done=true requires response."
            ),
        )


__all__ = ["AgentRuntime", "ParsedResponse"]
