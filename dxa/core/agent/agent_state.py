"""Agent state management."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from ..types import Objective, Plan, Signal, Step

@dataclass
class AgentState:
    """Maintains execution state."""
    
    # Initialize with default values using field
    objective: Optional[Objective] = None
    plan: Optional[Plan] = None
    working_memory: Dict[str, Any] = field(default_factory=dict)
    signals: List[Signal] = field(default_factory=list)
    current_step_idx: int = 0
    history: List[Any] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def set_objective(self, objective: Objective) -> None:
        """Set or update current objective"""
        self.objective = objective

    def set_plan(self, plan: Plan) -> None:
        """Set or update current plan"""
        self.plan = plan
        self.current_step_idx = 0

    def get_current_step(self) -> Optional[Step]:
        """Get current step being executed"""
        if self.plan and self.current_step_idx < len(self.plan.steps):
            return self.plan.steps[self.current_step_idx]
        return None

    def advance_step(self) -> None:
        """Move to next step"""
        self.current_step_idx += 1

    def add_signal(self, signal: Signal) -> None:
        """Add new signal"""
        self.signals.append(signal)

    def get_signals(self) -> List[Signal]:
        """Get all pending signals"""
        return self.signals

    def clear_signals(self) -> None:
        """Clear all processed signals"""
        self.signals.clear()

    def get_context(self) -> Dict[str, Any]:
        """Get current execution context"""
        return {
            "objective": self.objective,
            "working_memory": self.working_memory,
            "step_index": self.current_step_idx,
            "total_steps": len(self.plan.steps) if self.plan else 0
        }

    def update_working_memory(self, key: str, value: Any) -> None:
        """Update working memory"""
        self.working_memory[key] = value