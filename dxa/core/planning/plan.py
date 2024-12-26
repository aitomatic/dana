"""Plan implementation representing executable sequence of steps."""

from typing import Dict, List, cast
from datetime import datetime
from ..types import Objective
from ...common.graph import DirectedGraph

class Plan(DirectedGraph):
    """
    Executable plan represented as a directed graph where:
    - Nodes are steps to be executed
    - Edges define valid transitions between steps
    - Graph structure captures execution flow
    """
    def __init__(self, objective: Objective):
        super().__init__()
        self.objective = objective
        self.history: List[Dict] = []
    
    def update_plan(self, new_plan: 'Plan', reason: str) -> None:
        """Update current plan with changes from new plan.
        
        Args:
            new_plan: New plan to merge in
            reason: Reason for the update
        """
        # Store previous plan state
        previous_plan = cast(Plan, self.duplicate())

        self.history.append({
            'timestamp': datetime.now(),
            'reason': reason,
            'previous_plan': previous_plan,
            'new_plan': new_plan
        })
        
        self.objective = new_plan.objective
        self.nodes = new_plan.nodes
        self.edges = new_plan.edges
