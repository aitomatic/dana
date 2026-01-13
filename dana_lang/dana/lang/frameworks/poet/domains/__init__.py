"""
POET Domain System

This package provides the domain template system for POET function enhancement.
Domains define how functions are enhanced with Perceive→Operate→Enforce→Train patterns.

Built-in domains:
- computation: Mathematical operations with validation
- llm_optimization: LLM calls with retry and quality validation
- prompt_optimization: LLM prompts that learn from feedback
- ml_monitoring: ML model monitoring with adaptive thresholds

Usage:
    @poet(domain="computation", retries=2)
    def safe_divide(a: float, b: float) -> float:
        return a / b

    @poet(domain="computation:scientific", optimize_for="accuracy")  # Inheritance
    def scientific_calc(data: list[float]) -> float:
        return sum(data) / len(data)
"""

from .base import DomainTemplate, FunctionInfo
from .registry import DomainRegistry, register_domain

# Global registry instance
_registry = None


def get_registry() -> DomainRegistry:
    """Get the global domain registry instance"""
    global _registry
    if _registry is None:
        _registry = DomainRegistry()
    return _registry


def get_domain(name: str) -> DomainTemplate:
    """Get a domain template by name"""
    return get_registry().get_domain(name)


def list_domains() -> list[str]:
    """List all available domain names"""
    return get_registry().list_domains()


__all__ = [
    "DomainRegistry",
    "DomainTemplate",
    "FunctionInfo",
    "register_domain",
    "get_registry",
    "get_domain",
    "list_domains",
]
