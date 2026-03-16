from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage, LLMResponse
from dana.core.knowledge.prompts.codecs import AbstractCodec, CSXMLCodec, NativeToolsCodec
from dana.core.prompt.prompt_api import LocalPromptAPI
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
        self._system_prompt_template_override: str | None = None
        self._last_native_tools_state: bool | None = None  # Track for cache invalidation
        # Codec runtimes don't use json_mode — reconfigure the shared LLMCaller.
        self._llm_caller._json_mode = False

        # Reconfigure PromptBuilder for codec path:
        # - system_prompt_fn: lazy lambda so _prompt_api is resolved at call time
        # - context_position="append": codec appends context_line after system_prompt
        # - skip_retrieved_context=True: codec runtime doesn't inject <CONTEXT> user message
        from dana.core.prompt.prompt_builder import PromptBuilder

        self._prompt_builder = PromptBuilder(
            identity_fn=self.get_identity,
            template_fn=self.get_system_prompt_template,
            format_tool_fn=self.format_tool_for_prompt,
            system_prompt_fn=lambda: self._build_system_prompt(self._agent),
            context_position="append",
            skip_retrieved_context=True,
        )

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

    def set_system_prompt_template(self, template: str) -> None:
        """Override the entire system prompt template for codec runtimes.

        Sets the template on LocalPromptAPI. If prompt_api hasn't been
        created yet, stores it for deferred application.
        """
        self._system_prompt_template_override = template
        if self._prompt_api is not None:
            self._prompt_api.set_system_prompt_template(template)

    def _get_prompt_api(self, agent: STARAgent) -> LocalPromptAPI:
        if self._prompt_api is None:
            self._prompt_api = LocalPromptAPI(agent=agent, codec=self._codec, provider=self._provider)
            if self._system_prompt_template_override is not None:
                self._prompt_api.set_system_prompt_template(self._system_prompt_template_override)
        return self._prompt_api

    def _build_system_prompt(self, agent: STARAgent) -> str:
        prompt_api = self._get_prompt_api(agent)
        return prompt_api.system_prompt

    def call_llm(self, messages: list[LLMMessage]) -> LLMResponse:
        """Sync LLM call (no json_mode). Delegates to LLMCaller (observable fires there)."""
        return self._llm_caller.call_llm(messages)

    async def call_llm_async(self, messages: list[LLMMessage]) -> LLMResponse:
        """Async LLM call (no json_mode). Delegates to LLMCaller (observable fires there)."""
        return await self._llm_caller.call_llm_async(messages)

    def execute_tools(self, agent: STARAgent, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        res = super().execute_tools(agent, tool_calls)
        return res

    async def execute_tools_async(self, agent: STARAgent, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        res = await super().execute_tools_async(agent, tool_calls)
        return res
