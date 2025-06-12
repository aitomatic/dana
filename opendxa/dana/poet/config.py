"""
POET Configuration Profiles

This module provides predefined configuration profiles for common POET use cases,
making it easy to get started with appropriate settings for different scenarios.
"""

from typing import Any

from .poet import POETConfig


class POETProfiles:
    """Predefined POET configuration profiles for common use cases."""

    @staticmethod
    def development() -> POETConfig:
        """
        Development profile - optimized for development and testing.

        Features:
        - Lower retry counts for faster feedback
        - Shorter timeouts to catch issues quickly
        - Metrics collection enabled for debugging
        - Training disabled for predictable behavior
        """
        return POETConfig(retries=2, timeout=10.0, enable_training=False, collect_metrics=True)

    @staticmethod
    def production() -> POETConfig:
        """
        Production profile - optimized for reliability and performance.

        Features:
        - Higher retry counts for reliability
        - Reasonable timeouts for production workloads
        - Metrics collection enabled for monitoring
        - Training disabled for predictable behavior
        """
        return POETConfig(retries=3, timeout=30.0, enable_training=False, collect_metrics=True)

    @staticmethod
    def high_reliability() -> POETConfig:
        """
        High reliability profile - maximum fault tolerance.

        Features:
        - Maximum retry attempts
        - Extended timeouts for complex operations
        - Metrics collection for monitoring
        - Training disabled for consistency
        """
        return POETConfig(retries=5, timeout=60.0, enable_training=False, collect_metrics=True)

    @staticmethod
    def fast_execution() -> POETConfig:
        """
        Fast execution profile - optimized for speed.

        Features:
        - Minimal retries for speed
        - Short timeouts to fail fast
        - Lightweight metrics collection
        - Training disabled to avoid overhead
        """
        return POETConfig(retries=1, timeout=5.0, enable_training=False, collect_metrics=True)

    @staticmethod
    def learning_enabled() -> POETConfig:
        """
        Learning-enabled profile - with adaptive optimization.

        Features:
        - Moderate retries for learning opportunities
        - Reasonable timeouts for baseline establishment
        - Full metrics collection for learning
        - Training enabled for adaptive behavior
        """
        return POETConfig(retries=3, timeout=30.0, enable_training=True, collect_metrics=True)

    @staticmethod
    def minimal_overhead() -> POETConfig:
        """
        Minimal overhead profile - bare minimum POET pipeline.

        Features:
        - Single execution attempt
        - Very short timeout
        - No metrics collection
        - No training for minimal overhead
        """
        return POETConfig(retries=0, timeout=2.0, enable_training=False, collect_metrics=False)  # Single attempt only


class DomainProfiles:
    """Domain-specific configuration profiles."""

    @staticmethod
    def llm_optimization() -> POETConfig:
        """
        Configuration optimized for LLM operations.

        Features:
        - Higher timeout for LLM response times
        - Moderate retries for API reliability
        - Training enabled for prompt optimization
        - Domain plugin: llm_optimization
        """
        return POETConfig(retries=3, timeout=45.0, domain="llm_optimization", enable_training=True, collect_metrics=True)

    @staticmethod
    def building_management() -> POETConfig:
        """
        Configuration optimized for building management systems.

        Features:
        - High reliability for critical systems
        - Extended timeout for hardware operations
        - Training enabled for efficiency optimization
        - Domain plugin: building_management
        """
        return POETConfig(retries=4, timeout=20.0, domain="building_management", enable_training=True, collect_metrics=True)

    @staticmethod
    def financial_services() -> POETConfig:
        """
        Configuration optimized for financial operations.

        Features:
        - Maximum reliability for financial accuracy
        - Moderate timeout for market data operations
        - Training enabled for performance optimization
        - Domain plugin: financial_services
        """
        return POETConfig(retries=5, timeout=15.0, domain="financial_services", enable_training=True, collect_metrics=True)

    @staticmethod
    def semiconductor() -> POETConfig:
        """
        Configuration optimized for semiconductor operations.

        Features:
        - High precision and reliability
        - Extended timeout for complex calculations
        - Training enabled for process optimization
        - Domain plugin: semiconductor
        """
        return POETConfig(retries=4, timeout=60.0, domain="semiconductor", enable_training=True, collect_metrics=True)


def create_custom_profile(
    profile_name: str,
    retries: int = 3,
    timeout: float = 30.0,
    domain: str | None = None,
    enable_training: bool = False,
    collect_metrics: bool = True,
    **kwargs,
) -> POETConfig:
    """
    Create a custom POET configuration profile.

    Args:
        profile_name: Name for the custom profile (for documentation)
        retries: Number of retry attempts
        timeout: Timeout in seconds
        domain: Domain plugin to use
        enable_training: Enable T-stage learning
        collect_metrics: Enable metrics collection
        **kwargs: Additional configuration options

    Returns:
        Custom POET configuration

    Example:
        ```python
        # Create custom profile for API operations
        api_config = create_custom_profile(
            "api_operations",
            retries=3,
            timeout=20.0,
            enable_training=False
        )

        @poet_with_config(api_config)
        def call_external_api():
            # API call logic
            pass
        ```
    """
    config = POETConfig(retries=retries, timeout=timeout, domain=domain, enable_training=enable_training, collect_metrics=collect_metrics)

    # Add profile name to config for debugging
    config._profile_name = profile_name

    return config


def get_profile_recommendations(use_case: str) -> dict[str, Any]:
    """
    Get configuration profile recommendations for a specific use case.

    Args:
        use_case: Description of the use case

    Returns:
        Dictionary with recommended profiles and explanations

    Example:
        ```python
        recommendations = get_profile_recommendations("API calls with retries")
        print(recommendations["recommended"])  # "production"
        print(recommendations["alternatives"])  # ["high_reliability", "fast_execution"]
        ```
    """
    use_case_lower = use_case.lower()

    # Simple keyword-based recommendations
    recommendations = {"recommended": "production", "alternatives": [], "explanation": "", "domain_suggestions": []}

    # Development-related keywords
    if any(keyword in use_case_lower for keyword in ["dev", "test", "debug", "experiment"]):
        recommendations["recommended"] = "development"
        recommendations["alternatives"] = ["minimal_overhead", "fast_execution"]
        recommendations["explanation"] = "Development profile provides fast feedback with debugging capabilities"

    # Production-related keywords
    elif any(keyword in use_case_lower for keyword in ["prod", "deploy", "live", "production"]):
        recommendations["recommended"] = "production"
        recommendations["alternatives"] = ["high_reliability"]
        recommendations["explanation"] = "Production profile balances reliability with performance"

    # Performance-related keywords
    elif any(keyword in use_case_lower for keyword in ["fast", "speed", "quick", "performance"]):
        recommendations["recommended"] = "fast_execution"
        recommendations["alternatives"] = ["minimal_overhead", "production"]
        recommendations["explanation"] = "Fast execution profile minimizes latency and overhead"

    # Reliability-related keywords
    elif any(keyword in use_case_lower for keyword in ["reliable", "critical", "fault", "retry"]):
        recommendations["recommended"] = "high_reliability"
        recommendations["alternatives"] = ["production", "learning_enabled"]
        recommendations["explanation"] = "High reliability profile maximizes fault tolerance"

    # Learning-related keywords
    elif any(keyword in use_case_lower for keyword in ["learn", "adapt", "optimize", "improve"]):
        recommendations["recommended"] = "learning_enabled"
        recommendations["alternatives"] = ["production"]
        recommendations["explanation"] = "Learning enabled profile adapts behavior over time"

    # Domain-specific suggestions
    if any(keyword in use_case_lower for keyword in ["llm", "ai", "model", "prompt"]):
        recommendations["domain_suggestions"].append("llm_optimization")

    if any(keyword in use_case_lower for keyword in ["building", "hvac", "iot", "sensor"]):
        recommendations["domain_suggestions"].append("building_management")

    if any(keyword in use_case_lower for keyword in ["finance", "bank", "trading", "money"]):
        recommendations["domain_suggestions"].append("financial_services")

    if any(keyword in use_case_lower for keyword in ["chip", "semiconductor", "hardware", "fab"]):
        recommendations["domain_suggestions"].append("semiconductor")

    return recommendations


def poet_with_config(config: POETConfig):
    """
    Decorator factory that uses a pre-configured POET configuration.

    Args:
        config: POET configuration to use

    Returns:
        Decorator function

    Example:
        ```python
        # Use predefined profile
        prod_config = POETProfiles.production()

        @poet_with_config(prod_config)
        def my_function():
            return "result"

        # Use custom profile
        custom_config = create_custom_profile(
            "my_use_case",
            retries=5,
            timeout=60.0
        )

        @poet_with_config(custom_config)
        def another_function():
            return "result"
        ```
    """
    from .poet import POETExecutor

    def decorator(func):
        executor = POETExecutor(config)
        return executor(func)

    return decorator


# Convenience aliases for common profiles
dev = POETProfiles.development
prod = POETProfiles.production
reliable = POETProfiles.high_reliability
fast = POETProfiles.fast_execution
learning = POETProfiles.learning_enabled
minimal = POETProfiles.minimal_overhead

# Domain profile aliases
llm = DomainProfiles.llm_optimization
building = DomainProfiles.building_management
finance = DomainProfiles.financial_services
semiconductor = DomainProfiles.semiconductor
