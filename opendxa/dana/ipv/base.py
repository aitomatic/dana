"""
Base classes and interfaces for the IPV (Infer-Process-Validate) pattern.

This module defines the core abstractions that all IPV implementations must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional


class IPVPhaseType(Enum):
    """Types of IPV phases."""

    INFER = "infer"
    PROCESS = "process"
    VALIDATE = "validate"


class ReliabilityLevel(Enum):
    """How consistent should outputs be?"""

    LOW = "low"  # Creative variation encouraged
    MEDIUM = "medium"  # Consistent structure, varied content
    HIGH = "high"  # Consistent format, slight content variation
    MAXIMUM = "maximum"  # Same input = same output


class PrecisionLevel(Enum):
    """How exact should responses be?"""

    LOOSE = "loose"  # Broad strokes, creative interpretation
    GENERAL = "general"  # High-level, approximate, conceptual
    SPECIFIC = "specific"  # Detailed but allows reasonable interpretation
    EXACT = "exact"  # Precise numbers, specific facts, no approximations


class SafetyLevel(Enum):
    """How cautious should the system be?"""

    LOW = "low"  # Creative content, casual interactions
    MEDIUM = "medium"  # General analysis, recommendations
    HIGH = "high"  # Business decisions, public communications
    MAXIMUM = "maximum"  # Medical, legal, financial advice


class StructureLevel(Enum):
    """How formatted should output be?"""

    FREE = "free"  # Natural language, minimal formatting
    ORGANIZED = "organized"  # Logical flow, some formatting
    FORMATTED = "formatted"  # Consistent organization, clear sections
    STRICT = "strict"  # Exact JSON schema, specific formats


class ContextLevel(Enum):
    """How much background detail?"""

    MINIMAL = "minimal"  # Just the answer, no extra context
    STANDARD = "standard"  # Basic context, essential information
    DETAILED = "detailed"  # Good context, some examples, clear reasoning
    MAXIMUM = "maximum"  # Full background, examples, methodology


@dataclass
class IPVConfig:
    """Configuration for IPV phases and operations."""

    # 5-Dimension optimization settings
    reliability: ReliabilityLevel = ReliabilityLevel.HIGH
    precision: PrecisionLevel = PrecisionLevel.SPECIFIC
    safety: SafetyLevel = SafetyLevel.MEDIUM
    structure: StructureLevel = StructureLevel.ORGANIZED
    context: ContextLevel = ContextLevel.STANDARD

    # Phase-specific configurations
    infer_config: Dict[str, Any] = field(default_factory=dict)
    process_config: Dict[str, Any] = field(default_factory=dict)
    validate_config: Dict[str, Any] = field(default_factory=dict)

    # Custom functions for each phase
    infer_function: Optional[Callable] = None
    process_function: Optional[Callable] = None
    validate_function: Optional[Callable] = None

    # General settings
    max_iterations: int = 3
    timeout_seconds: Optional[float] = None
    debug_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary format."""
        return {
            "reliability": self.reliability.value,
            "precision": self.precision.value,
            "safety": self.safety.value,
            "structure": self.structure.value,
            "context": self.context.value,
            "infer_config": self.infer_config,
            "process_config": self.process_config,
            "validate_config": self.validate_config,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds,
            "debug_mode": self.debug_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IPVConfig":
        """Create config from dictionary."""
        config = cls()

        # Handle enum conversions
        if "reliability" in data:
            config.reliability = ReliabilityLevel(data["reliability"])
        if "precision" in data:
            config.precision = PrecisionLevel(data["precision"])
        if "safety" in data:
            config.safety = SafetyLevel(data["safety"])
        if "structure" in data:
            config.structure = StructureLevel(data["structure"])
        if "context" in data:
            config.context = ContextLevel(data["context"])

        # Handle other fields
        for field_name in ["infer_config", "process_config", "validate_config", "max_iterations", "timeout_seconds", "debug_mode"]:
            if field_name in data:
                setattr(config, field_name, data[field_name])

        return config


@dataclass
class IPVResult:
    """Result from an IPV phase execution."""

    success: bool
    result: Any
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None

    def is_success(self) -> bool:
        """Check if the phase execution was successful."""
        return self.success and self.error is None


class IPVPhase(ABC):
    """
    Abstract base class for all IPV phases.

    Each phase implements one part of the Infer-Process-Validate pattern:
    - INFER: Liberal input acceptance and context collection
    - PROCESS: Generous transformation and execution
    - VALIDATE: Conservative output guarantee
    """

    def __init__(self, phase_type: IPVPhaseType):
        self.phase_type = phase_type
        self._debug_mode = False

    @abstractmethod
    def execute(self, input_data: Any, context: Any, config: IPVConfig) -> IPVResult:
        """
        Execute this IPV phase.

        Args:
            input_data: The input to this phase
            context: Execution context (e.g., SandboxContext for Dana)
            config: IPV configuration

        Returns:
            IPVResult with the phase execution result
        """
        pass

    def set_debug_mode(self, enabled: bool) -> None:
        """Enable or disable debug mode for this phase."""
        self._debug_mode = enabled

    def _log_debug(self, message: str, **kwargs) -> None:
        """Log debug information if debug mode is enabled."""
        if self._debug_mode:
            print(f"[{self.phase_type.value.upper()}] {message}", **kwargs)

    def validate_config(self, config: IPVConfig) -> None:
        """
        Validate that the configuration is appropriate for this phase.

        Args:
            config: IPV configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(config, IPVConfig):
            raise ValueError(f"Expected IPVConfig, got {type(config)}")

    def get_phase_config(self, config: IPVConfig) -> Dict[str, Any]:
        """Get the configuration specific to this phase."""
        if self.phase_type == IPVPhaseType.INFER:
            return config.infer_config
        elif self.phase_type == IPVPhaseType.PROCESS:
            return config.process_config
        elif self.phase_type == IPVPhaseType.VALIDATE:
            return config.validate_config
        else:
            return {}


class IPVError(Exception):
    """Base exception for IPV-related errors."""

    def __init__(self, message: str, phase: Optional[IPVPhaseType] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.phase = phase
        self.original_error = original_error


class IPVConfigurationError(IPVError):
    """Raised when IPV configuration is invalid."""

    pass


class IPVExecutionError(IPVError):
    """Raised when IPV phase execution fails."""

    pass


class IPVValidationError(IPVError):
    """Raised when IPV validation fails."""

    pass
