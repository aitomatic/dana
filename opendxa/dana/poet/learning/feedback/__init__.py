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

from .feedback import FeedbackMode, SimulationFeedback
from .models import DomainSimulationModel, SimulationModel
from .providers import (
    FeedbackProvider,
    HybridFeedbackProvider,
    RealWorldFeedbackProvider,
    SafeTestingFeedbackProvider,
    SimulationFeedbackProvider,
)

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
