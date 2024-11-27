"""Internal LLM implementation for DXA agents.

This module provides a specialized LLM implementation for use within agents.
It handles agent-specific prompting and context management, distinct from
external LLM resources.

Example:
    ```python
    from dxa.agents.agent_llm import AgentLLM
    
    llm = AgentLLM(
        name="math_agent_llm",
        config={
            "model": "gpt-4",
            "api_key": "your-key"
        },
        agent_prompts={
            "system_prompt": "You are a mathematical reasoning expert...",
            "user_prompt": "Solve step by step: {query}"
        }
    )
    
    response = await llm.generate(
        context={"previous_steps": []},
        query="Solve: 2x + 5 = 13"
    )
    ```
"""

from typing import Dict, Any, Optional
from dxa.common.base_llm import BaseLLM

class AgentLLM(BaseLLM):
    """Internal agent LLM implementation.
    
    This class extends BaseLLM with agent-specific functionality, including
    customized prompting and context handling for agent operations.
    
    Attributes:
        agent_prompts: Dictionary of agent-specific prompt templates
        
    Args:
        name: Name for this LLM instance
        config: LLM configuration dictionary
        agent_prompts: Optional agent-specific prompts
        **kwargs: Additional arguments passed to BaseLLM
        
    Example:
        ```python
        llm = AgentLLM(
            name="research_agent_llm",
            config={"model": "gpt-4"},
            agent_prompts={
                "system_prompt": "You are a research assistant...",
                "user_prompt": "Research topic: {query}"
            }
        )
        ```
    """
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        agent_prompts: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """Initialize an agent's internal LLM."""
        super().__init__(name=name, config=config, **kwargs)
        self.agent_prompts = agent_prompts or {}
    
    # pylint: disable=unused-argument
    def get_system_prompt(self, context: Dict[str, Any], query: str) -> Optional[str]:
        """Get the system prompt for the agent LLM.
        
        Retrieves the system prompt from agent_prompts, optionally formatting
        it with context and query.
        
        Args:
            context: Current execution context
            query: Current query being processed
            
        Returns:
            Formatted system prompt if defined, None otherwise
            
        Example:
            ```python
            prompt = llm.get_system_prompt(
                context={"mode": "analysis"},
                query="Analyze this data"
            )
            ```
        """
        return self.agent_prompts.get("system_prompt")
    
    def get_user_prompt(self, context: Dict[str, Any], query: str) -> Optional[str]:
        """Get the user prompt for the agent LLM.
        
        Retrieves the user prompt from agent_prompts, optionally formatting
        it with context and query.
        
        Args:
            context: Current execution context
            query: Current query being processed
            
        Returns:
            Formatted user prompt if defined, None otherwise
            
        Example:
            ```python
            prompt = llm.get_user_prompt(
                context={"style": "detailed"},
                query="Explain neural networks"
            )
            ```
        """
        return self.agent_prompts.get("user_prompt")