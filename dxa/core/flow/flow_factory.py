"""Factory for creating flow components."""

from typing import Union
from .base_flow import BaseFlow
from .research_flow import ResearchFlow

class FlowFactory:
    """Creates flow components."""
    
    @classmethod
    def create_flow(cls, flow_type: Union[str, BaseFlow] = None) -> BaseFlow:
        """Create flow instance."""
        if isinstance(flow_type, BaseFlow):
            return flow_type
        flow_type = flow_type or "research"
        if flow_type == "research":
            return ResearchFlow()
        raise ValueError(f"Unknown flow type: {flow_type}") 