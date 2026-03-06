"""Runtime for native tool calling (Anthropic/OpenAI function calling)."""

from __future__ import annotations

from typing import Any

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMResponse
from dana.common.observable import observable
from dana.core.knowledge.prompts.codecs import AbstractCodec, NativeToolsCodec
from dana.core.llm.response_parser import _to_tool_call_dicts

from ..base import ParsedResponse
from .codec_base import CodecRuntimeBase


class CodecRuntimeWithNativeToolUse(CodecRuntimeBase):
    """
    Runtime for native tool calling (Anthropic/OpenAI function calling).

    This runtime is designed for LLM providers that support native function calling
    through their API (e.g., Anthropic's tool_use, OpenAI's function_calling).

    Validation is more flexible than XML-based runtimes:
    - Can have both response and tool_calls (LLM can explain while calling tools)
    - done=True cannot have pending tool_calls
    - done=False must have tool_calls
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0,
        max_tokens: int | None = None,
        llm: LLM | None = None,
        provider: str = "anthropic",
        codec: type[AbstractCodec] = NativeToolsCodec,
    ):
        # Always use native tools for this runtime
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            llm=llm,
            provider=provider,
            use_native_tools=True,
            codec=codec,
        )

    def validate_done_output(self, done: bool | None, has_tool_calls: bool, has_response: bool) -> str:
        """Validate the output format and return the next action.

        Native tools mode uses more flexible validation:
        - Having both response and tool_calls is valid (LLM can explain while calling tools)
        - done=True cannot have pending tool_calls
        - done=False must have tool_calls

        Args:
            done: Whether the LLM indicated it's done (True/False/None if invalid).
            has_tool_calls: Whether tool calls are present.
            has_response: Whether a response is present.

        Returns:
            One of "exit", "continue", or "retry".
        """
        if done is None:
            return "retry"

        if done and has_tool_calls:
            return "retry"  # Can't be done with pending tool calls

        if not done and not has_tool_calls:
            return "retry"  # Not done but no tools - invalid

        return "exit" if done else "continue"

    @observable
    def parse_response(self, response: LLMResponse) -> ParsedResponse:
        """Parse an LLM response for native tool calling.

        Extracts tool_calls from the API response (response.tool_calls) and
        parses <thinking> from content using the codec. No XML tool call parsing.

        Args:
            response: The raw LLM response.

        Returns:
            ParsedResponse with done, reasoning, response, tool_calls, etc.
        """
        content = str(response.content).strip() if response.content else ""
        tool_calls: list[dict[str, Any]] = []
        reasoning = None
        response_text = None

        # 1. Check for native tool calls from API response
        #    (Both OpenAI and Anthropic providers return tool_calls in compatible format)
        if response.tool_calls:
            tool_calls.extend(_to_tool_call_dicts(response.tool_calls))

        # 2. Check for provider's reasoning_content (e.g., DeepSeek, future Claude extended thinking)
        #    This takes precedence over XML tag parsing since it's the native format
        if response.reasoning_content:
            reasoning = response.reasoning_content
            # Still parse content for response_text (if any text content beyond reasoning)
            if content:
                parsed_codec_response = self._codec.parse_response(content)
                response_text = parsed_codec_response.response
        elif content:
            # 3. Fall back to codec parsing (XML <thinking> tags)
            parsed_codec_response = self._codec.parse_response(content)
            reasoning = parsed_codec_response.thinking
            response_text = parsed_codec_response.response

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
