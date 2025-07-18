"""
Domain-specific configuration wizards for POET.

This module provides pre-configured POET setups for common domains
to make POET more accessible and intuitive for users.
"""

from typing import Any


def financial_services(**kwargs) -> dict[str, Any]:
    """
    Pre-configured POET setup for financial services domain.

    Automatically configures:
    - FCRA compliance checking
    - Financial data validation
    - Risk assessment
    - Audit logging

    Args:
        **kwargs: Additional configuration to override defaults

    Returns:
        Configuration dictionary for @poet() decorator
    """
    config = {
        "domain": "financial_services",
        "perceive": {
            "input_validation": True,
            "financial_data_validation": True,
            "risk_assessment": True,
            "compliance_check": True,
        },
        "operate": {
            "retries": 3,
            "timeout": 30,
            "fail_safe": True,
        },
        "enforce": {
            "output_validation": True,
            "compliance_check": "FCRA",
            "audit_logging": True,
            "result_validation": True,
        },
        "train": {
            "learning_rate": 0.1,
            "feedback_threshold": 0.8,
            "model_updates": True,
        },
        "performance_tracking": True,
    }

    # Override with user-provided configuration
    config.update(kwargs)
    return config


def healthcare(**kwargs) -> dict[str, Any]:
    """
    Pre-configured POET setup for healthcare domain.

    Automatically configures:
    - HIPAA compliance checking
    - Medical data validation
    - Enhanced security measures
    - Clinical decision support

    Args:
        **kwargs: Additional configuration to override defaults

    Returns:
        Configuration dictionary for @poet() decorator
    """
    config = {
        "domain": "healthcare",
        "perceive": {
            "input_validation": True,
            "medical_data_validation": True,
            "privacy_scrubbing": True,
            "unit_conversion": True,
        },
        "operate": {
            "retries": 2,
            "timeout": 45,
            "fail_safe": True,
        },
        "enforce": {
            "output_validation": True,
            "compliance_check": "HIPAA",
            "clinical_validation": True,
            "safety_checks": True,
        },
        "train": {
            "learning_rate": 0.05,
            "feedback_threshold": 0.9,
            "clinical_feedback": True,
        },
        "performance_tracking": True,
    }

    config.update(kwargs)
    return config


def retail_ecommerce(**kwargs) -> dict[str, Any]:
    """
    Pre-configured POET setup for retail/e-commerce domain.

    Automatically configures:
    - Product recommendation optimization
    - Inventory management
    - Customer behavior analysis
    - Performance optimization

    Args:
        **kwargs: Additional configuration to override defaults

    Returns:
        Configuration dictionary for @poet() decorator
    """
    config = {
        "domain": "retail_ecommerce",
        "perceive": {
            "input_validation": True,
            "product_normalization": True,
            "price_validation": True,
            "inventory_check": True,
        },
        "operate": {
            "retries": 2,
            "timeout": 15,
            "caching": True,
        },
        "enforce": {
            "output_validation": True,
            "price_consistency": True,
            "inventory_validation": True,
            "recommendation_quality": True,
        },
        "train": {
            "learning_rate": 0.2,
            "feedback_threshold": 0.7,
            "recommendation_learning": True,
        },
        "performance_tracking": True,
    }

    config.update(kwargs)
    return config


def data_processing(**kwargs) -> dict[str, Any]:
    """
    Pre-configured POET setup for data processing domain.

    Automatically configures:
    - Data quality validation
    - ETL pipeline optimization
    - Error handling and recovery
    - Performance monitoring

    Args:
        **kwargs: Additional configuration to override defaults

    Returns:
        Configuration dictionary for @poet() decorator
    """
    config = {
        "domain": "data_processing",
        "perceive": {
            "input_validation": True,
            "data_quality_check": True,
            "schema_validation": True,
            "null_handling": True,
        },
        "operate": {
            "retries": 3,
            "timeout": 60,
            "batch_processing": True,
        },
        "enforce": {
            "output_validation": True,
            "data_quality_assurance": True,
            "completeness_check": True,
            "consistency_validation": True,
        },
        "train": {
            "learning_rate": 0.15,
            "feedback_threshold": 0.85,
            "pattern_learning": True,
        },
        "performance_tracking": True,
    }

    config.update(kwargs)
    return config


def security(**kwargs) -> dict[str, Any]:
    """
    Pre-configured POET setup for security domain.

    Automatically configures:
    - Threat detection optimization
    - Security policy enforcement
    - Incident response automation
    - Compliance monitoring

    Args:
        **kwargs: Additional configuration to override defaults

    Returns:
        Configuration dictionary for @poet() decorator
    """
    config = {
        "domain": "security",
        "perceive": {
            "input_validation": True,
            "threat_detection": True,
            "anomaly_detection": True,
            "payload_inspection": True,
        },
        "operate": {
            "retries": 1,  # Security operations should be quick
            "timeout": 10,
            "fail_secure": True,
        },
        "enforce": {
            "output_validation": True,
            "security_policy_check": True,
            "compliance_validation": True,
            "risk_assessment": True,
        },
        "train": {
            "learning_rate": 0.1,
            "feedback_threshold": 0.9,
            "threat_learning": True,
        },
        "performance_tracking": True,
    }

    config.update(kwargs)
    return config


# Convenience functions for common configurations
def quick_setup(domain: str, **kwargs) -> dict[str, Any]:
    """
    Quick setup for common domains with minimal configuration.

    Args:
        domain: Domain name (financial_services, healthcare, retail_ecommerce, etc.)
        **kwargs: Additional configuration options

    Returns:
        Configuration dictionary for @poet() decorator
    """
    domain_configs = {
        "financial_services": financial_services,
        "healthcare": healthcare,
        "retail_ecommerce": retail_ecommerce,
        "data_processing": data_processing,
        "security": security,
    }

    if domain in domain_configs:
        return domain_configs[domain](**kwargs)
    else:
        # Generic configuration for unknown domains
        return {"domain": domain, "retries": 2, "timeout": 30, "performance_tracking": True, **kwargs}


def poet_for_domain(domain: str, **kwargs):
    """
    Create a POET decorator pre-configured for a specific domain.

    This is a convenience function that combines domain wizard configuration
    with the POET decorator.

    Args:
        domain: Domain name
        **kwargs: Additional configuration options

    Returns:
        Configured POET decorator function
    """
    from dana.frameworks.poet.core.decorator import poet

    config = quick_setup(domain, **kwargs)
    return poet(**config)
