"""Base flow interface defining workflow patterns."""

from typing import List, Optional, Dict, Any, Union
from ..types import Step, Plan, Objective, ObjectiveStatus
from ..state import FlowState

class BaseFlow():
    """Base class for workflow patterns.
    
    Flows define the high-level pattern of work, while Plans handle
    the concrete execution strategy. Flows guide planning by:
    - Providing step templates
    - Suggesting next steps based on state
    - Validating plan transitions
    - Offering recovery patterns
    """
    
    def __init__(self, objective: Union[str, Objective]):
        if isinstance(objective, str):
            self.objective = Objective(original=objective, current=objective, status=ObjectiveStatus.INITIAL)
        else:
            self.objective = objective

        self.state = FlowState()

    def get_step_templates(self) -> List[Step]:
        """Get the template steps for this workflow pattern."""
        pass

    def suggest_next_steps(self, current_plan: Plan, world_state: Dict[str, Any]) -> List[Step]:
        """Suggest possible next steps based on current state."""
        pass

    def validate_plan(self, plan: Plan) -> bool:
        """Validate if plan follows flow constraints."""
        pass

    def get_recovery_steps(self, failed_step: Step) -> Optional[List[Step]]:
        """Get recovery steps if something fails."""
        pass 