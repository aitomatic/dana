from __future__ import annotations

from typing import Any

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage, LLMResponse
from dana.common.observable import observable
from dana.core.agent.components import PromptEngineer, ToolCaller
from dana.core.runtime import AgentRuntime, ParsedResponse


class LegacyRuntime(AgentRuntime):
    def __init__(self, llm: LLM | None = None):
        self._llm = llm
        self._agent = None
        self._prompt_engineer: PromptEngineer | None = None
        self._tool_caller: ToolCaller | None = None
        self._last_llm_response: LLMResponse | None = None

    @property
    def llm(self) -> LLM | None:
        return self._llm

    def set_llm(self, llm: LLM) -> None:
        self._llm = llm

    def get_output_instructions(self) -> str:
        return ""

    def public_description(self, agent) -> str:
        self._ensure_components(agent)
        return self._prompt_engineer.public_description

    def private_identity(self, agent) -> str:
        self._ensure_components(agent)
        return self._prompt_engineer.identity

    def system_prompt(self, agent) -> str:
        self._ensure_components(agent)
        return self._prompt_engineer.system_prompt

    @observable
    def build_prompt(self, agent, timeline, learned_context: str | None = None) -> list[LLMMessage]:
        self._ensure_components(agent)
        return self._prompt_engineer.build_llm_request(timeline)

    @observable
    def call_llm(self, messages: list[LLMMessage]) -> str:
        llm = self._resolve_llm()
        response = llm.chat_response_sync(
            messages,
            agent_id=self._agent.object_id if self._agent else None,
            agent_type=self._agent.agent_type if self._agent else None,
            temperature=0,
        )
        self._last_llm_response = response
        return response.content

    @observable
    async def call_llm_async(self, messages: list[LLMMessage]) -> str:
        llm = self._resolve_llm()
        response = await llm.chat_response(
            messages,
            agent_id=self._agent.object_id if self._agent else None,
            agent_type=self._agent.agent_type if self._agent else None,
            temperature=0,
        )
        self._last_llm_response = response
        return response.content

    @observable
    def parse_response(self, raw: str) -> ParsedResponse:
        if self._last_llm_response is None:
            return ParsedResponse(done=None, reasoning=None, response=None, tool_calls=[])
        response, reasoning, tool_calls, done = self._tool_caller.parse_llm_response(self._last_llm_response)
        return ParsedResponse(done=done, reasoning=reasoning, response=response, tool_calls=tool_calls)

    @observable
    def execute_tools(self, agent, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self._ensure_components(agent)
        return self._tool_caller.execute_tool_calls(tool_calls)

    @observable
    async def execute_tools_async(self, agent, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self._ensure_components(agent)
        return await self._tool_caller.async_execute_tool_calls(tool_calls)

    def reset(self) -> None:
        if self._prompt_engineer is not None:
            self._prompt_engineer.reset()

    def _resolve_llm(self) -> LLM:
        if self._llm is not None:
            return self._llm
        if self._agent is not None and getattr(self._agent, "_llm_client", None) is not None:
            return self._agent.llm_client
        self._llm = LLM()
        if self._agent is not None:
            self._agent.llm_client = self._llm
        return self._llm

    def _ensure_components(self, agent) -> None:
        if self._agent is agent and self._prompt_engineer and self._tool_caller:
            return
        self._agent = agent
        self._prompt_engineer = PromptEngineer(agent)
        self._tool_caller = ToolCaller(agent)
