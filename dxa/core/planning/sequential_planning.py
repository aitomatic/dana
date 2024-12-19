from typing import Dict, Any
from dxa.core.planning.base_planning import BasePlanning

class SequentialPlanning(BasePlanning):
    """Simple planning strategy that implements basic sequential planning."""
    
    def plan(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute simple sequential planning strategy.
        
        Returns:
            Dict[str, Any]: The planning result
        """
        raise NotImplementedError("Subclass must implement plan method")