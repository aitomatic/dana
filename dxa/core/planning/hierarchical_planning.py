from typing import Dict, Any
from dxa.core.planning.base_planning import BasePlanning

class HierarchicalPlanning(BasePlanning):
    """Hierarchical planning strategy that decomposes problems into subtasks."""
    
    def plan(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute hierarchical decomposition planning strategy.
        
        Returns:
            Dict[str, Any]: The planning result
        """
        raise NotImplementedError("Subclass must implement plan method")