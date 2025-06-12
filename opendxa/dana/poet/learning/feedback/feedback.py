"""
Core feedback data structures for enhanced POET Training stage.

This module defines the fundamental data types for multi-modal feedback
including simulation feedback, feedback modes, and performance metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FeedbackMode(Enum):
    """Operating modes for feedback generation"""
    
    REAL_WORLD = "real_world"      # Use actual sensors, user feedback, system metrics
    SIMULATION = "simulation"       # Use domain-specific simulation models
    HYBRID = "hybrid"              # Combine real-world + simulation feedback  
    SAFE_TESTING = "safe_testing"  # Constrained simulation for development/testing


@dataclass
class SimulationFeedback:
    """Rich feedback from simulation/real-world combination"""
    
    # Core performance metrics
    performance_score: float        # Overall system performance (0.0-1.0)
    user_satisfaction: float        # User/stakeholder satisfaction (0.0-1.0)
    system_efficiency: float        # Resource utilization efficiency (0.0-1.0)
    safety_score: float            # Safety and compliance score (0.0-1.0)
    
    # Domain-specific metrics (extensible)
    domain_metrics: dict[str, float] = field(default_factory=dict)
    
    # Simulation metadata
    feedback_mode: FeedbackMode = FeedbackMode.REAL_WORLD
    simulation_confidence: float = 1.0    # Confidence in feedback quality
    real_data_available: bool = True      # Whether real data was used
    model_accuracy: float = 1.0           # Estimated model accuracy
    
    # Contextual information
    scenario_context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Error and diagnostic information
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def overall_quality(self) -> float:
        """Calculate overall feedback quality score"""
        base_quality = (
            self.performance_score * 0.4 +
            self.user_satisfaction * 0.3 +
            self.system_efficiency * 0.2 +
            self.safety_score * 0.1
        )
        
        # Adjust based on confidence and data availability
        confidence_factor = self.simulation_confidence if self.feedback_mode != FeedbackMode.REAL_WORLD else 1.0
        data_factor = 1.0 if self.real_data_available else 0.9
        accuracy_factor = self.model_accuracy if self.feedback_mode != FeedbackMode.REAL_WORLD else 1.0
        
        return base_quality * confidence_factor * data_factor * accuracy_factor
    
    def has_errors(self) -> bool:
        """Check if feedback contains errors"""
        return len(self.errors) > 0
    
    def is_reliable(self) -> bool:
        """Check if feedback is reliable for learning"""
        return (
            self.overall_quality() > 0.5 and
            not self.has_errors() and
            self.simulation_confidence > 0.6
        )


@dataclass 
class FeedbackRequest:
    """Request for feedback generation"""
    
    # Function execution context
    function_name: str
    function_input: dict[str, Any]
    function_output: Any
    execution_context: dict[str, Any]
    
    # Feedback requirements
    requested_mode: FeedbackMode
    domain: str | None = None
    required_metrics: list[str] = field(default_factory=list)
    
    # Timing and constraints
    timeout_seconds: float = 30.0
    min_confidence: float = 0.5
    
    # Additional context
    user_context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FeedbackCapabilities:
    """Describes feedback provider capabilities"""
    
    supported_modes: list[FeedbackMode]
    supported_domains: list[str]
    available_metrics: list[str]
    simulation_models: list[str]
    
    # Performance characteristics
    typical_latency_ms: float
    confidence_range: tuple[float, float]  # (min, max)
    accuracy_estimate: float
    
    # Requirements
    requires_real_data: bool = False
    requires_user_input: bool = False
    requires_domain_config: bool = False 