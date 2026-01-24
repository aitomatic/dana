from abc import ABC, abstractmethod

from dana.common.schemas.tool_call import MethodSignature, ParsedCodecResponse, ToolCall


class AbstractCodec(ABC):
    @classmethod
    @abstractmethod
    def get_instruction(cls) -> str:
        """
        Get the instruction for the codec (response format contract).
        """
        pass

    @classmethod
    @abstractmethod
    def construct(cls, signature: MethodSignature) -> str:
        """
        Construct a formatted string from a method signature.
        """
        pass

    @classmethod
    @abstractmethod
    def parse_method_call(cls, xml_string: str) -> ToolCall:
        """
        Parse a method call from a formatted string.
        """
        pass

    @classmethod
    @abstractmethod
    def parse_response(cls, xml_string: str) -> ParsedCodecResponse:
        """
        Parse LLM response and extract thinking, tool calls, and response.

        Args:
            xml_string: Raw LLM response text (may be XML or other format depending on codec)

        Returns:
            ParsedCodecResponse with thinking, tool_calls, and response fields.
        """
        pass
