"""
POET (Perceive → Operate → Enforce → Train) Framework

POE-focused implementation providing immediate value through the core
Perceive → Operate → Enforce pipeline, with optional T-stage learning.
"""

from .mvp_poet import (
    POEConfig,
    POEExecutor,
    POEMetrics,
    poet,
    # Legacy compatibility
    SimplePOETConfig,
    SimplePOETExecutor,
)

from .errors import (
    # Base error classes
    POEError,
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
    POEProfiles,
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

from .metrics import (
    # Metrics classes
    POEExecutionMetrics,
    POEMetricsCollector,
    # Utility functions
    get_global_collector,
    record_execution_metrics,
)

__all__ = [
    # Core POE classes
    "POEConfig",
    "POEExecutor",
    "POEMetrics",
    "poet",
    # Legacy compatibility
    "SimplePOETConfig",
    "SimplePOETExecutor",
    # Error types
    "POEError",
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
    "POEProfiles",
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
    "POEExecutionMetrics",
    "POEMetricsCollector",
    # Utility functions
    "get_global_collector",
    "record_execution_metrics",
]

__version__ = "0.2.0"  # Bumped for POE-focused refactoring
