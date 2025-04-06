"""Resource executor for tool execution."""

from typing import Dict, Any, List

class ResourceExecutor:
    """Executes resources for tool calling."""

    async def execute_resources(self, prompt: str, context: Any) -> List[Dict[str, Any]]:
        """Execute resources based on prompt and context.
        
        Args:
            prompt: The prompt to execute
            context: The execution context
            
        Returns:
            List of tool responses
        """
        # For now, return empty list as tool execution is not implemented
        return [] 