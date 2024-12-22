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
        """Create a reasoning system with the given configuration."""
        if reasoner_type is None:
            return DirectReasoner()
        if isinstance(reasoner_type, BaseReasoner):
            return reasoner_type
        if reasoner_type not in cls.REASONER_TYPES:
            raise ValueError(f"Unknown reasoner type: {reasoner_type}")
        return cls.REASONER_TYPES[reasoner_type]() 
