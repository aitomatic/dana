"""
Native Tools Codec for LLM native function calling.

This codec is designed for use with LLM providers that support native
tool/function calling (OpenAI, Anthropic). Tool calls are made through
the API rather than parsed from text output.
"""

import re
from typing import override

from dana.common.schemas.tool_call import MethodSignature, ParameterInfo, ParsedCodecResponse, ToolCall
from dana.core.knowledge.prompts.codecs.abstract_codec import AbstractCodec


class NativeToolsCodec(AbstractCodec):
    """
    Codec for native LLM tool calling (OpenAI/Anthropic function calling).

    Key differences from CSXMLCodec:
    - get_instruction(): Requires <thinking> block, plain text response (no XML tags)
    - construct(): Tool descriptions without XML usage examples
    - parse_response(): Extracts thinking, returns plain text as response
    - Tool calls come from LLM API response, not parsed from text
    """

    @classmethod
    @override
    def get_instruction(cls) -> str:
        """
        Response format instruction for native tool calling mode.

        Keeps <thinking> block for reasoning but uses plain text for response.
        Tool calls are made through the LLM's native function calling feature.
        """
        return """
RESPONSE FORMAT:
1. Start with a <thinking> block for your internal reasoning
2. After </thinking>, write your response as plain text

<thinking>
/* PRIVATE — NOT SHOWN TO USER
   Brief analysis:
   • What does the user need?
   • Do I have enough info? If not, call the appropriate tool.
   • My approach to answer or which tool to call.
   END PRIVATE */
</thinking>

Your response to the user goes here as plain text.
No special tags needed for the response.

RULES:
• <thinking> is ALWAYS required for internal reasoning
• After </thinking>, write your response directly (no XML tags)
• To call a tool, use the function calling feature (not XML)
"""

    @classmethod
    @override
    def construct(cls, signature: MethodSignature) -> str:
        """
        Format a method signature for display in the prompt.

        Simplified format without XML usage examples since tools are
        called through the native API.
        """
        # Use custom tool_name if provided via @named_tool, else use object_id:method format
        if signature.tool_name:
            tool_identifier = signature.tool_name
        else:
            identifier = signature.object_id or signature.class_name
            tool_identifier = f"{identifier}:{signature.name}"

        return "\n".join(
            [
                f"### {tool_identifier}",
                f"Description: {signature.description}",
                "Parameters:",
                cls._parameters_to_str(signature.parameters),
                # NO "Usage:" section with XML example - tools called via native API
            ]
        )

    @classmethod
    def _parameters_to_str(cls, parameters: list[ParameterInfo]) -> str:
        """Format parameters list for display."""
        text = ""
        for parameter in parameters:
            required = "(required)" if not parameter.has_default else ""
            text += f"- {parameter.name}: {required} {parameter.description}\n"
        return text

    @classmethod
    @override
    def parse_method_call(cls, xml_string: str) -> ToolCall:
        """
        Not used for native tools - tool calls come from LLM API response.

        Raises:
            NotImplementedError: Always, since native tools don't use text-based tool calls.
        """
        raise NotImplementedError(
            "NativeToolsCodec does not parse tool calls from text. Tool calls should be extracted from the LLM API response."
        )

    @classmethod
    @override
    def parse_response(cls, xml_string: str) -> ParsedCodecResponse:
        """
        Parse response containing <thinking> block and plain text.

        Extracts:
        - thinking: Content within <thinking>...</thinking> tags
        - response: Everything after </thinking> tag

        Tool calls are not extracted here - they come from the LLM API response.

        Args:
            xml_string: Raw LLM response text

        Returns:
            ParsedCodecResponse with thinking and response fields.
            tool_calls is always None (handled by runtime from API response).
        """
        thinking = None
        response = xml_string

        # Extract thinking block
        thinking_match = re.search(r"<thinking>(.*?)</thinking>", xml_string, re.DOTALL)
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # Remove XML comments from thinking
            thinking = re.sub(r"<!--.*?-->", "", thinking, flags=re.DOTALL).strip()
            # Response is everything after </thinking>
            response = xml_string[thinking_match.end() :].strip()
        else:
            # Try to extract thinking without closing tag
            thinking_fallback = cls._extract_thinking_without_closing_tag(xml_string)
            if thinking_fallback:
                thinking = thinking_fallback

        # Clean up response - remove any remaining XML comments
        if response:
            response = re.sub(r"<!--.*?-->", "", response, flags=re.DOTALL).strip()

        # Tool calls come from native API, not text parsing
        # Ensure thinking is always a string (required by ParsedCodecResponse)
        return ParsedCodecResponse(thinking=thinking or "", tool_calls=None, response=response if response else None)

    @classmethod
    def _extract_thinking_without_closing_tag(cls, xml_string: str) -> str | None:
        """
        Extract thinking content when closing tag is missing.

        Args:
            xml_string: Raw LLM response text

        Returns:
            Extracted thinking content, or None if not found.
        """
        opening_match = re.search(r"<thinking>", xml_string)
        if not opening_match:
            return None

        start_pos = opening_match.end()
        # Take everything after <thinking> as thinking content
        thinking = xml_string[start_pos:].strip()
        if thinking:
            thinking = re.sub(r"<!--.*?-->", "", thinking, flags=re.DOTALL).strip()
        return thinking if thinking else None
