"""Internal LLM implementation for DXA agents. 

This LLM is used internally by agents, not to be confused with the LLMs
that are external resources.
"""

from typing import Dict, Any, Optional
from dxa.common.base_llm import BaseLLM

class AgentLLM(BaseLLM):
    """Internal agent LLM implementation."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        agent_prompts: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """Initialize an agent's internal LLM.
        
        Args:
            name: Name for this LLM instance
            config: LLM configuration dictionary
            agent_prompts: Optional agent-specific prompts
            **kwargs: Additional arguments passed to BaseLLM
        """
        super().__init__(name=name, config=config, **kwargs)
        self.agent_prompts = agent_prompts or {}
    
    # pylint: disable=unused-argument
    def get_system_prompt(self, context: Dict[str, Any], query: str) -> Optional[str]:
        """Get the system prompt for the agent LLM.
        
        Args:
            context: Current context
            query: Current query
            
        Returns:
            System prompt if defined, None otherwise
        """
        return self.agent_prompts.get("system_prompt")
    
    def get_user_prompt(self, context: Dict[str, Any], query: str) -> Optional[str]:
        """Get the user prompt for the agent LLM.
        
        Args:
            context: Current context
            query: Current query
            
        Returns:
            User prompt if defined, None otherwise
        """
        return self.agent_prompts.get("user_prompt")