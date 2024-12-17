"""Core types for strategic and tactical reasoning."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

# Strategic Types
@dataclass
class Objective:
    """Strategic objective with evolution tracking."""
    original: str
    current: str
    constraints: List[str]
    success_criteria: List[str]
    context: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    def update(self, new_state: str, reason: str, evidence: Dict[str, Any]):
        """Record objective evolution."""
        self.history.append({
            "from": self.current,
            "to": new_state,
            "reason": reason,
            "evidence": evidence,
            "timestamp": datetime.now()
        })
        self.current = new_state

@dataclass
class Plan:
    """Strategic execution plan."""
    steps: List[Dict[str, Any]]
    rationale: str
    current_index: int = 0
    resources_needed: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def current_step(self) -> Optional[Dict[str, Any]]:
        """Get current execution step."""
        return self.steps[self.current_index] if self.steps else None

    def update(self, new_steps: List[Dict[str, Any]], reason: str):
        """Update plan while preserving history."""
        self.history.append({
            "old_steps": self.steps,
            "new_steps": new_steps,
            "reason": reason,
            "timestamp": datetime.now()
        })
        self.steps = new_steps
        self.current_index = 0

# Tactical Types
@dataclass
class ExecutionContext:
    """Tactical execution context."""
    resources: Dict[str, Any]
    workspace: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class StepResult:
    """Result from tactical step execution."""
    success: bool
    output: Any
    confidence: float
    discoveries: List[Dict[str, Any]] = field(default_factory=list)
    resource_updates: Dict[str, Any] = field(default_factory=dict)

# Interaction Types
class InteractionMode(str, Enum):
    """Supported interaction modes."""
    AUTONOMOUS = "autonomous"  # Self-directed
    INTERACTIVE = "interactive"  # User-guided
    COLLABORATIVE = "collaborative"  # Multi-agent 