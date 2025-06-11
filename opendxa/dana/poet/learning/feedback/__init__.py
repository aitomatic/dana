"""
POET Feedback and Simulation Infrastructure

This module provides the base classes and interfaces for enhanced Training stage
capabilities including simulation models, multi-modal feedback, and domain-specific
feedback providers.

Components:
- FeedbackProvider: Base interface for feedback generation
- SimulationFeedback: Rich feedback data structure
- FeedbackMode: Operating modes for feedback generation
- SimulationModel: Base class for domain simulation models
"""

from .providers import (
    FeedbackProvider,
    RealWorldFeedbackProvider,
    SimulationFeedbackProvider,
    HybridFeedbackProvider,
    SafeTestingFeedbackProvider,
)
from .feedback import SimulationFeedback, FeedbackMode
from .models import SimulationModel, DomainSimulationModel

__all__ = [
    # Core interfaces
    "FeedbackProvider",
    "SimulationFeedback",
    "FeedbackMode",
    "SimulationModel",
    # Provider implementations
    "RealWorldFeedbackProvider",
    "SimulationFeedbackProvider",
    "HybridFeedbackProvider",
    "SafeTestingFeedbackProvider",
    # Base simulation models
    "DomainSimulationModel",
]
