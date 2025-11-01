from abc import ABC, abstractmethod

from dana.common.schemas.tool_call import MethodSignature, ToolCall


class AbstractCodec(ABC):
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