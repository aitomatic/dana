"""Runtime for XML-based tool calling (CSXMLCodec, KLXMLCodec)."""

from __future__ import annotations

from typing import Any

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMResponse
from dana.common.observable import observable
from dana.core.knowledge.prompts.codecs import AbstractCodec, CSXMLCodec

from ..base import ParsedResponse
from .codec import CodecRuntimeBase


class CodecRuntimeWithoutNativeToolUse(CodecRuntimeBase):
    """
    Runtime for XML-based tool calling (CSXMLCodec, KLXMLCodec).

    This runtime is designed for XML-based codecs that encode tool calls
    as XML tags within the LLM's text response (e.g., <function_call>).

    Validation is stricter than native tool use runtimes:
    - done=True requires response, no tool_calls
    - done=False requires tool_calls, no response
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0,
        max_tokens: int | None = None,
        llm: LLM | None = None,
        provider: str = "anthropic",
        codec: type[AbstractCodec] = CSXMLCodec,
    ):
        # Never use native tools for this runtime
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            llm=llm,
            provider=provider,
            use_native_tools=False,
            codec=codec,
        )

    def validate_done_output(self, done: bool | None, has_tool_calls: bool, has_response: bool) -> str:
        """Validate the output format and return the next action.

        XML codec mode uses stricter validation:
        - done=True requires response, no tool_calls
        - done=False requires tool_calls, no response

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
        """Parse an LLM response for XML-based tool calling.

        Parses tool_calls from XML using codec.parse_response().
        Extracts <thinking>, <response>, <function_call> from text.

        Args:
            response: The raw LLM response.

        Returns:
            ParsedResponse with done, reasoning, response, tool_calls, etc.
        """
        content = str(response.content).strip() if response.content else ""
        tool_calls: list[dict[str, Any]] = []
        reasoning = None
        response_text = None

        # Parse content for thinking/response/tool_calls using codec
        if content:
            parsed_codec_response = self._codec.parse_response(content)
            reasoning = parsed_codec_response.thinking
            response_text = parsed_codec_response.response

            # Extract tool_calls from XML
            # (XML codecs return tool_calls from parsed text)
            if parsed_codec_response.tool_calls:
                for tc in parsed_codec_response.tool_calls:
                    # Use tool_name if set (custom name), otherwise build identifier:method
                    if tc.tool_name:
                        function_name = tc.tool_name
                    else:
                        identifier = tc.object_id or tc.class_name
                        function_name = f"{identifier}:{tc.name}" if identifier else tc.name
                    tool_calls.append({"function": function_name, "arguments": tc.parameters})

        # Determine done flag based on tool calls
        # - If there are tool calls, we're not done (need to execute them)
        # - If no tool calls, we're done (can return response)
        done = len(tool_calls) == 0

        return ParsedResponse(
            done=done,
            reasoning=reasoning,
            response=response_text if response_text else None,
            tool_calls=tool_calls,
            todo_list=[],
        )
