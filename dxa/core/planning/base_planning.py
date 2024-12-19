from typing import Dict, Any

class BasePlanning:
    """Base class for all planning strategies."""
    
    def plan(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the planning strategy.
        
        Returns:
            Dict[str, Any]: The planning result
        """
        raise NotImplementedError("Subclass must implement plan method")