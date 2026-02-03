from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage, LLMResponse
from dana.common.observable import observable
from dana.core.agent.timeline import TimelineProtocol
from dana.core.knowledge.prompts import LocalPromptAPI
from dana.core.knowledge.prompts.codecs import AbstractCodec, CSXMLCodec, NativeToolsCodec
from dana.core.runtime.base import AgentRuntime

from ..base import ParsedResponse


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent


class CodecRuntimeBase(AgentRuntime):
    """
    Abstract base class for codec-based runtimes.

    Provides shared functionality for encoding and decoding messages.
    Subclasses must implement validate_done_output() and parse_response().
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
        # Auto-detect use_native_tools based on codec type if not explicitly set
        if use_native_tools is None:
            use_native_tools = codec is NativeToolsCodec

        super().__init__(
            model=model, temperature=temperature, max_tokens=max_tokens, llm=llm, provider=provider, use_native_tools=use_native_tools
        )
        self._codec = codec
        self._prompt_api = None
        self._last_native_tools_state: bool | None = None  # Track for cache invalidation

    @abstractmethod
    def validate_done_output(self, done: bool | None, has_tool_calls: bool, has_response: bool) -> str:
        """Validate the output format and return the next action.

        Args:
            done: Whether the LLM indicated it's done (True/False/None if invalid).
            has_tool_calls: Whether tool calls are present.
            has_response: Whether a response is present.

        Returns:
            One of "exit", "continue", or "retry".
        """
        ...

    @abstractmethod
    def parse_response(self, response: LLMResponse) -> ParsedResponse:
        """Parse an LLM response into a structured ParsedResponse.

        Args:
            response: The raw LLM response.

        Returns:
            ParsedResponse with done, reasoning, response, tool_calls, etc.
        """
        ...

    def _get_prompt_api(self, agent: STARAgent) -> LocalPromptAPI:
        if self._prompt_api is None:
            self._prompt_api = LocalPromptAPI(agent=agent, codec=self._codec)
        return self._prompt_api

    def _build_system_prompt(self, agent: STARAgent) -> str:
        prompt_api = self._get_prompt_api(agent)
        return prompt_api.system_prompt

    @observable
    def build_prompt(self, agent, timeline: TimelineProtocol, learned_context: str | None = None) -> list[LLMMessage]:
        self._agent = agent
        messages = []

        # Build native tools first (affects system prompt choice)
        self._build_native_tools_if_supported(agent)

        # Build tool name registry for @named_tool decorated methods
        self._build_tool_name_registry(agent)

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

        if self._agent._reminder_manager:
            reminders = self._agent._reminder_manager.evaluate_all(self._agent, timeline)
            if reminders:
                messages.append(LLMMessage(role="user", content=reminders))

        self._log_prompt_build(agent, system_prompt, timeline, messages)

        return messages

    @observable
    def call_llm(self, messages: list[LLMMessage]) -> LLMResponse:
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
        return response

    @observable
    async def call_llm_async(self, messages: list[LLMMessage]) -> LLMResponse:
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
        return response

    def execute_tools(self, agent: STARAgent, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        res = super().execute_tools(agent, tool_calls)
        return res

    async def execute_tools_async(self, agent: STARAgent, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        res = await super().execute_tools_async(agent, tool_calls)
        return res


class CodecRuntime(CodecRuntimeBase):
    """
    Backward-compatible runtime that auto-selects behavior based on use_native_tools.

    DEPRECATED: Use CodecRuntimeWithNativeToolUse or CodecRuntimeWithoutNativeToolUse directly
    for explicit control over the runtime behavior.

    This class maintains backward compatibility by implementing both native and non-native
    tool use modes based on the use_native_tools parameter.
    """

    def validate_done_output(self, done: bool | None, has_tool_calls: bool, has_response: bool) -> str:
        """Validate the output format and return the next action.

        For native tools mode, the validation is less strict:
        - Having both response and tool_calls is valid (LLM can explain while calling tools)
        - done=False requires tool_calls
        - done=True requires response (no pending tool calls)
        """
        if done is None:
            return "retry"

        if self._use_native_tools:
            # Native tools mode: more flexible validation
            if done and has_tool_calls:
                return "retry"  # Can't be done with pending tool calls
            if not done and not has_tool_calls:
                return "retry"  # Not done but no tools - invalid
            return "exit" if done else "continue"

        # XML codec mode: stricter validation (original behavior)
        if done and has_tool_calls:
            return "retry"
        if not done and has_response:
            return "retry"
        if not done and not has_tool_calls:
            return "retry"
        if done and not has_response:
            return "retry"
        return "exit" if done else "continue"

    @observable
    def parse_response(self, response: LLMResponse) -> ParsedResponse:
        content = str(response.content).strip() if response.content else ""
        tool_calls: list[dict[str, Any]] = []
        reasoning = None
        response_text = None
        done = None

        # 1. Check for native tool calls from API response FIRST
        #    (Both OpenAI and Anthropic providers return tool_calls in compatible format)
        if response.tool_calls:
            tool_calls.extend(self._to_tool_call_dicts(response.tool_calls))

        # 2. Parse content for thinking/response using codec
        #    (Works for both CSXMLCodec and NativeToolsCodec)
        if content:
            parsed_codec_response = self._codec.parse_response(content)
            reasoning = parsed_codec_response.thinking
            response_text = parsed_codec_response.response

            # 3. Extract tool_calls from XML if NOT using native tools
            #    (XML codecs return tool_calls from parsed text)
            if not self._use_native_tools and parsed_codec_response.tool_calls:
                for tc in parsed_codec_response.tool_calls:
                    # Use tool_name if set (custom name), otherwise build identifier:method
                    if tc.tool_name:
                        function_name = tc.tool_name
                    else:
                        identifier = tc.object_id or tc.class_name
                        function_name = f"{identifier}:{tc.name}" if identifier else tc.name
                    tool_calls.append({"function": function_name, "arguments": tc.parameters})

        # 4. Determine done flag based on tool calls
        #    - If there are tool calls, we're not done (need to execute them)
        #    - If no tool calls, we're done (can return response)
        done = len(tool_calls) == 0

        return ParsedResponse(
            done=done,
            reasoning=reasoning,
            response=response_text if response_text else None,
            tool_calls=tool_calls,
            todo_list=[],
        )
