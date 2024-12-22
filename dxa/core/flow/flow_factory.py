"""Factory for creating DXA flows."""

from typing import Dict, Any
from ..core.flow import BaseFlow

class FlowFactory:
    """Creates and configures DXA flows."""

    FLOW_TYPES = {
        "none": BaseFlow,
    }

    @classmethod
    def create_flow(cls, config: Dict[str, Any]) -> BaseFlow:
        """Create a flow with the given configuration."""
        flow_type = config.get("type", "none")
        if flow_type not in cls.FLOW_TYPES:
            raise ValueError(f"Unknown flow type: {flow_type}")
        return cls.FLOW_TYPES[flow_type](**config) 