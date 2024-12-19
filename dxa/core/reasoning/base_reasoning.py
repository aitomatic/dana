from typing import Any, Dict

class BaseReasoning:
    """Base class for all reasoning strategies."""
    
    async def reason_about(self, task: Any, context: Dict) -> Any:
        """Execute reasoning strategy on given task.
        
        Args:
            task: The task to reason about
            context: Execution context
            
        Returns:
            Reasoning result
        """
        raise NotImplementedError("Subclass must implement reason_about method")