from typing import Any

from pydantic import BaseModel

class ParsedArgKwargsResults(BaseModel):
    matched_args: list[Any]
    matched_kwargs: dict[str, Any]
    varargs: list[Any]
    varkwargs: dict[str, Any]
    unmatched_args: list[Any]
    unmatched_kwargs: dict[str, Any]


class ParameterInfo(BaseModel):
    """Information about a single method parameter."""
    name: str
    type: str
    type_object: Any | None = None  # Actual type object for programmatic use
    description: str
    has_default: bool
    default: Any | None = None
    example: str | None = None
    
    def __getitem__(self, key: str) -> Any:
        """Support dictionary-like access for backward compatibility."""
        return getattr(self, key)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Support dict.get() for backward compatibility."""
        return getattr(self, key, default)
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator for backward compatibility."""
        return hasattr(self, key)


class MethodSignature(BaseModel):
    """Structured information about a method signature."""
    class_name: str | None = None
    name: str
    description: str
    parameters: list[ParameterInfo]
    
    def __getitem__(self, key: str) -> Any:
        """Support dictionary-like access for backward compatibility."""
        return getattr(self, key)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Support dict.get() for backward compatibility."""
        return getattr(self, key, default)
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator for backward compatibility."""
        return hasattr(self, key)

class ToolCall(BaseModel):
    class_name: str | None = None
    name: str
    parameters: dict[str, Any]


class ParsedCodecResponse(BaseModel):
    thinking: str
    tool_calls: list[ToolCall] | None = None