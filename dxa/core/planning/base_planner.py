"""
Core interfaces defining how Planning and Reasoning interact
with objectives, plans, steps, and signals.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any

from ..types import Objective, Plan, Signal
from ..workflow import BaseFlow

class BasePlanner(ABC):
    """
    Planning is responsible for:
    1. Creating plans from objectives
    2. Updating plans based on signals
    3. Evolving objectives when needed
    """
    
    def __init__(self, flow: Optional[BaseFlow] = None):
        self.flow = flow
        self._current_step_index = 0
        self._world_state: Dict[str, Any] = {}

    def get_world_state(self) -> Dict[str, Any]:
        """Get current world state."""
        return self._world_state

    def update_world_state(self, updates: Dict[str, Any]) -> None:
        """Update world state with new information."""
        self._world_state.update(updates)

    @abstractmethod
    async def create_plan(self, objective: Objective) -> Plan:
        """
        Create initial plan for the objective.
        
        Args:
            objective: The objective to create a plan for
            
        Returns:
            Plan: The created plan
        """
        pass

    @abstractmethod
    def process_signals(
        self,
        plan: Plan,
        signals: List[Signal]
    ) -> Tuple[Optional[Plan], List[Signal]]:
        """
        Process signals and optionally return updated plan and new signals.
        
        Args:
            plan: Current plan being executed
            signals: List of signals to process
            
        Returns:
            Tuple containing:
            - Optional[Plan]: Updated plan if steps need to change
            - List[Signal]: New signals if objective needs to evolve
        """
        pass

    def set_flow(self, flow: BaseFlow) -> None:
        """Update flow pattern."""
        self.flow = flow