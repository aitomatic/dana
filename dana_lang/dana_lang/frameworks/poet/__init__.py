"""POET Framework - Perceive-Operate-Enforce-Transform

Implementation focusing on core transpilation and learning capabilities.
"""

# Core POET components
# Configuration and setup utilities
from .config import (
    data_processing,
    financial_services,
    healthcare,
    poet_for_domain,
    quick_setup,
    retail_ecommerce,
    security,
)
from .core import POETConfig, POETEnhancer, POETError, POETResult, POETTranspilationError, poet
from .domains import DomainRegistry
from . import enforce, operate, perceive, train

# Development and testing utilities
from .utils import (
    POETPhaseDebugger,
    POETTestMode,
    debug_poet_function,
    performance_benchmark,
    test_poet_function,
)

__all__ = [
    # Core POET
    "poet",
    "POETConfig",
    "POETResult",
    "POETEnhancer",
    "POETError",
    "POETTranspilationError",
    "DomainRegistry",
    "perceive",
    "operate",
    "enforce",
    "train",
    # Domain wizards
    "financial_services",
    "healthcare",
    "retail_ecommerce",
    "data_processing",
    "security",
    "quick_setup",
    "poet_for_domain",
    # Testing and debugging
    "debug_poet_function",
    "test_poet_function",
    "performance_benchmark",
    "POETTestMode",
    "POETPhaseDebugger",
]
