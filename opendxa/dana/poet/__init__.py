"""
POET (Perceive → Operate → Enforce → Train) Framework

POE-focused implementation providing immediate value through the core
Perceive → Operate → Enforce pipeline, with optional T-stage learning.
"""

from .config import (
    DomainProfiles,
    # Profile classes
    POETProfiles,
    building,
    # Utility functions
    create_custom_profile,
    # Convenience aliases
    dev,
    fast,
    finance,
    get_profile_recommendations,
    learning,
    llm,
    minimal,
    poet_with_config,
    prod,
    reliable,
    semiconductor,
)
from .errors import (
    ConfigurationError,
    # Specific error types
    DomainPluginError,
    EnforceError,
    InputValidationError,
    OperateError,
    OutputValidationError,
    ParameterLearningError,
    PerceiveError,
    # Base error classes
    POETError,
    RetryExhaustedError,
    TimeoutError,
    TrainError,
    create_context,
    # Utility functions
    wrap_poe_error,
)
from .metrics import (
    # Metrics classes
    POETExecutionMetrics,
    POETMetricsCollector,
    # Utility functions
    get_global_collector,
    record_execution_metrics,
)
from .plugins import (
    PLUGIN_REGISTRY,
    # Plugin system
    POETPlugin,
)
from .poet import (
    POEMetrics,
    POETConfig,
    POETExecutor,
    # Legacy compatibility
    SimplePOETConfig,
    SimplePOETExecutor,
    poet,
)

__all__ = [
    # Core POET classes
    "POETConfig",
    "POETExecutor",
    "POEMetrics",
    "poet",
    # Legacy compatibility
    "SimplePOETConfig",
    "SimplePOETExecutor",
    # Error types
    "POETError",
    "PerceiveError",
    "OperateError",
    "EnforceError",
    "TrainError",
    "DomainPluginError",
    "InputValidationError",
    "RetryExhaustedError",
    "TimeoutError",
    "OutputValidationError",
    "ParameterLearningError",
    "ConfigurationError",
    "wrap_poe_error",
    "create_context",
    # Configuration profiles
    "POETProfiles",
    "DomainProfiles",
    "create_custom_profile",
    "get_profile_recommendations",
    "poet_with_config",
    # Convenience aliases
    "dev",
    "prod",
    "reliable",
    "fast",
    "learning",
    "minimal",
    "llm",
    "building",
    "finance",
    "semiconductor",
    # Metrics classes
    "POETExecutionMetrics",
    "POETMetricsCollector",
    # Utility functions
    "get_global_collector",
    "record_execution_metrics",
    # Plugin system
    "POETPlugin",
    "PLUGIN_REGISTRY",
]

__version__ = "0.3.0"  # Unified poet decorator with advanced learning support
