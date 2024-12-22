"""Factory for creating DXA reasoning systems."""

from typing import Union
from . import BaseReasoner, DirectReasoner

class ReasonerFactory:
    """Creates and configures DXA reasoning systems."""

    REASONER_TYPES = {
        "none": BaseReasoner,
        "direct": DirectReasoner,
    }

    @classmethod
    def create_reasoner(cls, reasoner_type: Union[str, BaseReasoner] = None) -> BaseReasoner:
        """Create reasoner instance."""
        if isinstance(reasoner_type, BaseReasoner):
            return reasoner_type
        reasoner_type = reasoner_type or "direct"
        if reasoner_type == "direct":
            return DirectReasoner()
        raise ValueError(f"Unknown reasoner: {reasoner_type}")
