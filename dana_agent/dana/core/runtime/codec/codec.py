from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage
from dana.common.observable import observable
from dana.core.agent.timeline import TimelineProtocol
from dana.core.knowledge.prompts import LocalPromptAPI
from dana.core.knowledge.prompts.codecs import AbstractCodec, CSXMLCodec
from dana.core.runtime.base import AgentRuntime

from ..base import ParsedResponse, TodoItem


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent


class CodecRuntime(AgentRuntime):
    """
    Runtime for encoding and decoding messages.
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0,
        max_tokens: int | None = None,
        llm: LLM | None = None,
        provider: str = "anthropic",
        use_native_tools: bool | None = None,
        codec: type[AbstractCodec] = CSXMLCodec,
    ):
        super().__init__(
            model=model, temperature=temperature, max_tokens=max_tokens, llm=llm, provider=provider, use_native_tools=use_native_tools
        )
        self._codec = codec
        self._prompt_api = None

    # def validate_done_output(self, done: bool | None, has_tool_calls: bool, has_response: bool) -> str:
    #     return True

    def _get_prompt_api(self, agent: STARAgent) -> LocalPromptAPI:
        if self._prompt_api is None:
            self._prompt_api = LocalPromptAPI(agent=agent, codec=self._codec)
        return self._prompt_api

    def _build_system_prompt(self, agent: STARAgent) -> str:
        prompt_api = self._get_prompt_api(agent)
        return prompt_api.system_prompt

    def build_prompt(self, agent, timeline: TimelineProtocol, learned_context: str | None = None) -> list[LLMMessage]:
        self._agent = agent
        messages = []

        # Build native tools first (affects system prompt choice)
        self._build_native_tools_if_supported(agent)

        # Inject ephemeral runtime context
        runtime_context = self._get_runtime_context()
        if timeline:
            timeline.set_context(runtime_context)

        # Build system prompt with runtime context prepended
        # Mark system prompt for caching - it's static and often large
        system_prompt = self._build_system_prompt(agent)
        context_line = self._format_runtime_context(runtime_context)
        full_system_prompt = f"{system_prompt}\n\n{context_line}" if context_line else system_prompt
        messages.append(
            LLMMessage(
                role="system",
                content=full_system_prompt,
                cache_control={"type": "ephemeral"},  # Cache for Anthropic; OpenAI caches implicitly
            )
        )

        if timeline:
            timeline_messages = timeline.to_llm_messages()
            messages.extend(timeline_messages)

        self._log_prompt_build(agent, system_prompt, timeline, messages)

        return messages

    @observable
    def call_llm(self, messages: list[LLMMessage]) -> str:
        llm = self._resolve_llm()
        tools = self._native_tools if self._native_tools else None
        response = llm.chat_response_sync(
            messages,
            agent_id=self._agent.object_id if self._agent else None,
            agent_type=self._agent.agent_type if self._agent else None,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            tools=tools,
        )
        self._last_llm_response = response
        return response.content

    @observable
    async def call_llm_async(self, messages: list[LLMMessage]) -> str:
        llm = self._resolve_llm()
        tools = self._native_tools if self._native_tools else None
        response = await llm.chat_response(
            messages,
            agent_id=self._agent.object_id if self._agent else None,
            agent_type=self._agent.agent_type if self._agent else None,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            tools=tools,
        )
        self._last_llm_response = response
        return response.content

    @observable
    def parse_response(self, raw: str | dict | Any) -> ParsedResponse:
        if raw is None:
            return ParsedResponse(done=None, reasoning=None, response=None, tool_calls=[], todo_list=None)

        # Ensure raw is a string - LLM providers sometimes return unexpected types
        if not isinstance(raw, str):
            raw = str(raw)

        content = raw.strip()
        done = None
        response_text = None
        tool_calls: list[dict[str, Any]] = []
        todo_list: list[TodoItem] | None = None
        reasoning = None

        # Check for native tool calls from the LLM response
        if self._use_native_tools is False:
            parsed_codec_response = self._codec.parse_response(content)

            # Convert ToolCall objects to expected dict format for execute_tools
            if parsed_codec_response.tool_calls:
                for tc in parsed_codec_response.tool_calls:
                    # Build function name: "object_id:method" or "class_name:method"
                    identifier = tc.object_id or tc.class_name
                    if identifier:
                        function_name = f"{identifier}:{tc.name}"
                    else:
                        function_name = tc.name
                    tool_calls.append({"function": function_name, "arguments": tc.parameters})

            reasoning = parsed_codec_response.thinking  # Fixed: was .reasoning
            response_text = parsed_codec_response.response
            done = len(tool_calls) == 0  # Fixed: done=True only when no tool calls
            todo_list = []

        return ParsedResponse(
            done=done,
            reasoning=reasoning,
            response=response_text if response_text else None,
            tool_calls=tool_calls,
            todo_list=todo_list,
        )
