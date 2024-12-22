"""Factory for creating flow components."""

from typing import Dict, Any, Union
from .base_flow import BaseFlow
from .sequential_flow import SequentialFlow

class FlowFactory:
    """Creates flow components."""
    
    @classmethod
    def create_flow(cls, flow_type: Union[str, BaseFlow] = None) -> BaseFlow:
        """Create flow instance."""
        if isinstance(flow_type, BaseFlow):
            return flow_type
        flow_type = flow_type or "sequential"
        if flow_type == "sequential":
            return SequentialFlow()
        raise ValueError(f"Unknown flow type: {flow_type}") 