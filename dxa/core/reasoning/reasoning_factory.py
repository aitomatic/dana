"""Factory for creating reasoning patterns."""

from typing import Dict, Type
from .reasoning_pattern import ReasoningPattern
from .direct_reasoning import DirectReasoning
from .chain_of_thought_reasoning import ChainOfThoughtReasoning
from .ooda_reasoning import OODAReasoning
from .dana_reasoning import DANAReasoning

class ReasoningFactory:
    """Creates reasoning pattern instances."""
    
    PATTERNS: Dict[str, Type[ReasoningPattern]] = {
        "direct": DirectReasoning,
        "cot": ChainOfThoughtReasoning,
        "ooda": OODAReasoning,
        "dana": DANAReasoning
    }
    
    @classmethod
    def create(cls, pattern_type: str, **kwargs) -> ReasoningPattern:
        """Create a reasoning pattern instance."""
        if pattern_type not in cls.PATTERNS:
            raise ValueError(f"Unknown pattern: {pattern_type}")
        return cls.PATTERNS[pattern_type](**kwargs)
