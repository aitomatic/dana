"""
IPV (Infer-Process-Validate) Architecture for Dana

This module provides the core IPV pattern implementation for intelligent optimization
across all Dana operations, following Postel's Law: "Be liberal in what you accept,
be conservative in what you send."
"""

from .base import IPVConfig, IPVPhase
from .defaults import DefaultInferPhase, DefaultProcessPhase, DefaultValidatePhase

# Phase 3: IPVExecutor architecture
from .executor import IPVAPIIntegrator, IPVDataProcessor, IPVExecutor, IPVReason
from .orchestrator import IPVOrchestrator
from .phases import InferPhase, ProcessPhase, ValidatePhase

# Phase 2: Type-driven optimization components
from .type_inference import TypeInferenceEngine
from .type_optimization import TypeOptimizationProfile, TypeOptimizationRegistry, TypeOptimizationRule
from .validation import TypeValidator, ValidationResult

__all__ = [
    # Core interfaces
    "IPVPhase",
    "IPVConfig",
    # Phase implementations
    "InferPhase",
    "ProcessPhase",
    "ValidatePhase",
    # Orchestration
    "IPVOrchestrator",
    # Default implementations
    "DefaultInferPhase",
    "DefaultProcessPhase",
    "DefaultValidatePhase",
    # Type-driven optimization (Phase 2)
    "TypeInferenceEngine",
    "TypeOptimizationRegistry",
    "TypeOptimizationRule",
    "TypeOptimizationProfile",
    "TypeValidator",
    "ValidationResult",
    # IPVExecutor architecture (Phase 3)
    "IPVExecutor",
    "IPVReason",
    "IPVDataProcessor",
    "IPVAPIIntegrator",
]

__version__ = "0.3.0"
