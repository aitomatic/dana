"""Factory for creating reasoning systems."""

from typing import Union
from dxa.core.reasoning import (
    BaseReasoning,
    DirectReasoning,
    ChainOfThoughtReasoning,
    OODAReasoning,
    DANAReasoning
)

class ReasoningFactory:
    """Factory for creating reasoning instances."""
    
    REASONING_TYPES = {
        "direct": DirectReasoning,
        "cot": ChainOfThoughtReasoning,
        "ooda": OODAReasoning,
        "dana": DANAReasoning
    }

    @classmethod
    def create(cls, reasoning_type: Union[str, BaseReasoning, None]) -> BaseReasoning:
        """Create a reasoning instance.
        
        Args:
            reasoning_type: String identifier, reasoning instance, or None
            
        Returns:
            BaseReasoning: Configured reasoning instance (DirectReasoning if None)
            
        Raises:
            ValueError: If reasoning type is unknown
        """
        if reasoning_type is None:
            return DirectReasoning()
            
        if isinstance(reasoning_type, BaseReasoning):
            return reasoning_type
            
        if reasoning_type not in cls.REASONING_TYPES:
            raise ValueError(f"Unknown reasoning type: {reasoning_type}")
            
        return cls.REASONING_TYPES[reasoning_type]() 