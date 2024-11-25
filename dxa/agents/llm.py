"""Internal LLM implementation for DXA agents. 

This LLM is used internally by agents, not to be confused with the LLMs
that are external resources.
"""

from typing import Dict, Any
from dxa.core.common.base_llm import BaseLLM

class AgentLLM(BaseLLM):
    """Internal agent LLM implementation."""
    
    def __init__(self, config: Dict[str, Any], name: str = None, **kwargs):
        """Initialize an agent's internal LLM.
        
        Args:
            config: LLM configuration dictionary
            name: Optional name for the LLM instance
            **kwargs: Additional arguments passed to BaseLLM
        """
        super().__init__()
        self.config = config
        self.name = name

    async def cleanup(self) -> None:
        """Clean up any resources used by the agent's LLM."""
        await super().cleanup()
        # Add any AgentLLM-specific cleanup here
        if hasattr(self, 'client'):
            await self.client.close()