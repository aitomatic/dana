"""
Core interfaces defining how Planning and Reasoning interact
with objectives, plans, steps, and signals.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from ..types import Objective, Plan, Signal


class BasePlanning(ABC):
    """
    Planning is responsible for:
    1. Creating plans from objectives
    2. Updating plans based on signals
    3. Evolving objectives when needed
    """
    
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
    async def process_signals(
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