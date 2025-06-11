"""
POET (Perceive → Operate → Enforce → Train) Framework

POE-focused implementation providing immediate value through the core
Perceive → Operate → Enforce pipeline, with optional T-stage learning.
"""

from .poet import (
    POETConfig,
    POETExecutor,
    POEMetrics,
    poet,
    # Legacy compatibility
    SimplePOETConfig,
    SimplePOETExecutor,
)

from .errors import (
    # Base error classes
    POETError,
    PerceiveError,
    OperateError,
    EnforceError,
    TrainError,
    # Specific error types
    DomainPluginError,
    InputValidationError,
    RetryExhaustedError,
    TimeoutError,
    OutputValidationError,
    ParameterLearningError,
    ConfigurationError,
    # Utility functions
    wrap_poe_error,
    create_context,
)

from .config import (
    # Profile classes
    POETProfiles,
    DomainProfiles,
    # Utility functions
    create_custom_profile,
    get_profile_recommendations,
    poet_with_config,
    # Convenience aliases
    dev,
    prod,
    reliable,
    fast,
    learning,
    minimal,
    llm,
    building,
    finance,
    semiconductor,
)

from .plugins import (
    # Plugin system
    POETPlugin,
    PLUGIN_REGISTRY,
)

from .metrics import (
    # Metrics classes
    POETExecutionMetrics,
    POETMetricsCollector,
    # Utility functions
    get_global_collector,
    record_execution_metrics,
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
