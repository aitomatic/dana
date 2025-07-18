"""POET Type Definitions"""

import builtins
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class POETConfig:
    """Configuration for POET function enhancement"""

    # Core configuration
    domain: str | None = None
    optimize_for: str | None = None  # When set, enables Train phase
    retries: int = 1
    timeout: float | None = None
    enable_monitoring: bool = True

    # Phase-specific configuration
    perceive: dict[str, Any] = field(default_factory=dict)
    operate: dict[str, Any] = field(default_factory=dict)
    enforce: dict[str, Any] = field(default_factory=dict)
    train: dict[str, Any] = field(default_factory=dict)

    # Observability and debugging
    debug: bool = False
    trace_phases: bool = False
    performance_tracking: bool = True

    def dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "domain": self.domain,
            "optimize_for": self.optimize_for,
            "retries": self.retries,
            "timeout": self.timeout,
            "enable_monitoring": self.enable_monitoring,
            "perceive": self.perceive,
            "operate": self.operate,
            "enforce": self.enforce,
            "train": self.train,
            "debug": self.debug,
            "trace_phases": self.trace_phases,
            "performance_tracking": self.performance_tracking,
        }

    @classmethod
    def from_dict(cls, data: builtins.dict[str, Any]) -> "POETConfig":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class TranspiledFunction:
    """Result of POET transpilation"""

    code: str
    language: str = "python"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(cls, response_data: dict[str, Any]) -> "TranspiledFunction":
        """Create from API response"""
        impl = response_data.get("poet_implementation", {})
        return cls(code=impl.get("code", ""), language=impl.get("language", "python"), metadata=response_data.get("metadata", {}))


class POETResult:
    """Simplified POET result that behaves like the original result but with POET metadata"""

    def __init__(
        self,
        result: Any,
        function_name: str,
        version: str = "v1",
        phase_timings: dict[str, float] | None = None,
        confidence: float | None = None,
    ):
        self._result = result
        self._poet = {
            "execution_id": str(uuid4()),
            "function_name": function_name,
            "version": version,
            "enhanced": True,
            "phase_timings": phase_timings or {},
            "confidence": confidence,
            "total_execution_time": sum(phase_timings.values()) if phase_timings else None,
        }

    @property
    def poet(self) -> dict[str, Any]:
        """Access POET metadata - cleaner than _poet"""
        return self._poet

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to wrapped result"""
        if name in self._poet:
            return self._poet[name]
        return getattr(self._result, name)

    def __getitem__(self, key: Any) -> Any:
        """Delegate item access to wrapped result"""
        return self._result[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        """Delegate item assignment to wrapped result"""
        self._result[key] = value

    def __eq__(self, other: Any) -> bool:
        """Compare POETResult with wrapped value"""
        return self._result == other

    def __ne__(self, other: Any) -> bool:
        """Not equal comparison"""
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Make POETResult hashable based on wrapped result"""
        return hash(self._result)

    def __bool__(self) -> bool:
        """Boolean evaluation based on wrapped result"""
        return bool(self._result)

    def __int__(self) -> int:
        """Integer conversion"""
        return int(self._result)

    def __float__(self) -> float:
        """Float conversion"""
        return float(self._result)

    def __str__(self) -> str:
        return str(self._result)

    def __repr__(self) -> str:
        return f"POETResult({self._result!r})"

    # Arithmetic operations - delegate to wrapped result
    def __add__(self, other: Any) -> Any:
        """Addition"""
        return self._result + other

    def __radd__(self, other: Any) -> Any:
        """Right addition"""
        return other + self._result

    def __sub__(self, other: Any) -> Any:
        """Subtraction"""
        return self._result - other

    def __rsub__(self, other: Any) -> Any:
        """Right subtraction"""
        return other - self._result

    def __mul__(self, other: Any) -> Any:
        """Multiplication"""
        return self._result * other

    def __rmul__(self, other: Any) -> Any:
        """Right multiplication"""
        return other * self._result

    def __truediv__(self, other: Any) -> Any:
        """Division"""
        return self._result / other

    def __rtruediv__(self, other: Any) -> Any:
        """Right division"""
        return other / self._result

    def __floordiv__(self, other: Any) -> Any:
        """Floor division"""
        return self._result // other

    def __rfloordiv__(self, other: Any) -> Any:
        """Right floor division"""
        return other // self._result

    def __mod__(self, other: Any) -> Any:
        """Modulo"""
        return self._result % other

    def __rmod__(self, other: Any) -> Any:
        """Right modulo"""
        return other % self._result

    def __pow__(self, other: Any) -> Any:
        """Power"""
        return self._result**other

    def __rpow__(self, other: Any) -> Any:
        """Right power"""
        return other**self._result

    def unwrap(self) -> Any:
        """Get the original result without POET wrapper (deprecated - use direct access)"""
        return self._result

    def raw(self) -> Any:
        """Get the raw result without POET wrapper - cleaner name"""
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
