"""
POET Learning System

Comprehensive learning framework for POET functions including:
- Formal objective functions and multi-objective optimization
- Online and batch learning algorithms
- Performance metrics and tracking
- Feedback processing and integration
"""

# Core learning components
# Feedback system
from .feedback import (
    FeedbackMode,
    FeedbackProvider,
    HybridFeedbackProvider,
    RealWorldFeedbackProvider,
    SimulationFeedback,
)
from .metrics import LearningMetrics, PerformanceTracker

# Objective framework
from .objective import (
    EvaluationContext,
    MultiObjective,
    ObjectiveEvaluationResult,
    ObjectiveEvaluator,
    ObjectiveFunction,
    ObjectivePriority,
    ObjectiveType,
    POETObjectiveRegistry,
    get_domain_objectives,
    get_global_registry,
)
from .online_learner import ExecutionFeedback, OnlineLearner

__all__ = [
    # Core learning
    "OnlineLearner",
    "ExecutionFeedback",
    "PerformanceTracker",
    "LearningMetrics",
    # Objective framework
    "ObjectiveType",
    "ObjectivePriority",
    "ObjectiveFunction",
    "MultiObjective",
    "ObjectiveEvaluationResult",
    "POETObjectiveRegistry",
    "ObjectiveEvaluator",
    "EvaluationContext",
    "get_global_registry",
    "get_domain_objectives",
    # Feedback system
    "FeedbackProvider",
    "SimulationFeedback",
    "FeedbackMode",
    "RealWorldFeedbackProvider",
    "HybridFeedbackProvider",
]
