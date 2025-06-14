"""POET Type Definitions"""

from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class POETConfig:
    """Configuration for POET function enhancement"""

    domain: Optional[str] = None
    optimize_for: Optional[str] = None  # When set, enables Train phase
    retries: int = 3
    timeout: float = 30.0
    enable_monitoring: bool = True

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "domain": self.domain,
            "optimize_for": self.optimize_for,
            "retries": self.retries,
            "timeout": self.timeout,
            "enable_monitoring": self.enable_monitoring,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "POETConfig":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class TranspiledFunction:
    """Result of POET transpilation"""

    code: str
    language: str = "python"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(cls, response_data: Dict[str, Any]) -> "TranspiledFunction":
        """Create from API response"""
        impl = response_data.get("poet_implementation", {})
        return cls(code=impl.get("code", ""), language=impl.get("language", "python"), metadata=response_data.get("metadata", {}))


class POETResult:
    """Wrapper for POET function results with execution context"""

    def __init__(self, result: Any, function_name: str, version: str = "v1"):
        self._result = result
        self._poet = {"execution_id": str(uuid4()), "function_name": function_name, "version": version, "enhanced": True}

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to wrapped result"""
        return getattr(self._result, name)

    def __getitem__(self, key: Any) -> Any:
        """Delegate item access to wrapped result"""
        return self._result[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        """Delegate item assignment to wrapped result"""
        self._result[key] = value

    def __repr__(self) -> str:
        return f"POETResult({self._result!r})"

    def __str__(self) -> str:
        return str(self._result)

    def unwrap(self) -> Any:
        """Get the original result without POET wrapper"""
        return self._result


class POETServiceError(Exception):
    """Base exception for POET service errors"""

    pass


class POETTranspilationError(POETServiceError):
    """Raised when function transpilation fails"""

    pass


class POETFeedbackError(POETServiceError):
    """Raised when feedback processing fails"""

    pass
