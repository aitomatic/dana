"""Internal LLM implementation for DXA agents. 

This LLM is used internally by agents, not to be confused with the LLMs
that are external resources.
"""

from typing import Dict, Any, Optional
from dxa.core.common.base_llm import BaseLLM

class AgentLLM(BaseLLM):
    """Internal agent LLM implementation."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        agent_prompts: Optional[Dict[str, str]] = None,
        name: str = None,
        **kwargs
    ):
        """Initialize an agent's internal LLM.
        
        Args:
            config: LLM configuration dictionary
            agent_prompts: Agent prompts dictionary
            name: Optional name for the LLM instance
            **kwargs: Additional arguments passed to BaseLLM
        """
        super().__init__(name=name, config=config, **kwargs)
        self.agent_prompts = agent_prompts
    
    # pylint: disable=unused-argument
    def get_system_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the system prompt for the agent LLM."""
        return self.agent_prompts["system_prompt"] if hasattr(self.agent_prompts, "system_prompt") else None
    
    def get_user_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the user prompt for the agent LLM."""
        return self.agent_prompts["user_prompt"] if hasattr(self.agent_prompts, "user_prompt") else None