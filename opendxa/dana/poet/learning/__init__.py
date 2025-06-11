"""
POET Learning System

Comprehensive learning framework for POET functions including:
- Formal objective functions and multi-objective optimization
- Online and batch learning algorithms
- Performance metrics and tracking
- Feedback processing and integration
"""

# Core learning components
from .online_learner import OnlineLearner, ExecutionFeedback
from .metrics import PerformanceTracker, LearningMetrics

# Objective framework
from .objective import (
    ObjectiveType,
    ObjectivePriority,
    ObjectiveFunction,
    MultiObjective,
    ObjectiveEvaluationResult,
    POETObjectiveRegistry,
    ObjectiveEvaluator,
    EvaluationContext,
    get_global_registry,
    get_domain_objectives,
)

# Feedback system
from .feedback import (
    FeedbackProvider,
    SimulationFeedback,
    FeedbackMode,
    RealWorldFeedbackProvider,
    HybridFeedbackProvider,
)

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
