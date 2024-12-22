"""Research workflow implementation."""

from typing import List, Dict, Any
from ..types import Step, Plan
from .base_flow import BaseFlow

class ResearchFlow(BaseFlow):
    """Research workflow pattern.
    
    Defines the standard research process:
    1. Gather information
    2. Analyze findings
    3. Synthesize insights
    4. Draw conclusions
    """
    
    def get_step_templates(self) -> List[Step]:
        return [
            Step(description="Gather information about {topic}", order=0),
            Step(description="Analyze gathered information", order=1),
            Step(description="Synthesize key findings", order=2),
            Step(description="Generate final conclusions", order=3)
        ]

    def suggest_next_steps(self, current_plan: Plan, world_state: Dict[str, Any]) -> List[Step]:
        """Suggest next steps based on research progress."""
        current_step = current_plan.get_current_step()
        if not current_step:
            # Starting fresh - use first template
            template = self.get_step_templates()[0]
            return [Step(
                description=template.description.format(
                    topic=current_plan.objective.current
                ),
                order=0
            )]
        # ... suggest based on progress 