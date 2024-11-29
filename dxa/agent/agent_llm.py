"""Agent-specific LLM implementation.

This module extends the base LLM functionality with agent-specific features,
particularly prompt management and context handling. It combines agent-specific
prompts with reasoning-specific prompts and manages the overall interaction
context.

Example:
    ```python
    llm = AgentLLM(
        name="agent_llm",
        config={"model": "gpt-4"},
        agent_prompts={
            "system_prompt": "You are an expert in {domain}...",
            "user_prompt": "Please analyze: {query}"
        }
    )
    
    # Prompts will be combined with reasoning-specific prompts
    response = await llm.query([
        {"role": "system", "content": "Additional reasoning instructions..."},
        {"role": "user", "content": "Specific task..."}
    ])
    ```
"""

from typing import Dict, Any, Optional, List
from dxa.common.base_llm import BaseLLM

class AgentLLM(BaseLLM):
    """LLM implementation specialized for agent operations.
    
    This class extends BaseLLM with agent-specific functionality, particularly:
    1. Management of agent-specific prompts
    2. Combination of agent and reasoning prompts
    3. Context handling across interactions
    4. Structured response formatting
    
    The key difference from BaseLLM is that AgentLLM handles the composition
    of prompts from multiple sources (agent, reasoning system) and manages
    the interaction context.
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
    
    async def query(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Query the LLM with combined agent and reasoning prompts."""
        combined_messages = []
        
        # Separate messages by source
        agent_messages = []
        reasoning_messages = []
        
        for msg in messages:
            if msg.get("source") == "reasoning":
                reasoning_messages.append(msg)
            else:
                agent_messages.append(msg)
        
        # Handle system messages
        system_content = []
        
        # Add agent system prompt first (if exists)
        if self.agent_prompts.get("system_prompt"):
            system_content.append(self.agent_prompts["system_prompt"])
            
        # Add reasoning system prompts
        system_content.extend(
            m["content"] for m in reasoning_messages 
            if m["role"] == "system"
        )
        
        # Add other system prompts
        system_content.extend(
            m["content"] for m in agent_messages 
            if m["role"] == "system"
        )
        
        if system_content:
            combined_messages.append({
                "role": "system",
                "content": "\n\n".join(system_content)
            })
        
        # Handle user messages
        user_content = []
        
        # Add agent user prompt first (if exists)
        if self.agent_prompts.get("user_prompt"):
            user_content.append(self.agent_prompts["user_prompt"])
            
        # Add reasoning user prompts
        user_content.extend(
            m["content"] for m in reasoning_messages 
            if m["role"] == "user"
        )
        
        # Add other user prompts
        user_content.extend(
            m["content"] for m in agent_messages 
            if m["role"] == "user"
        )
        
        if user_content:
            combined_messages.append({
                "role": "user",
                "content": "\n\n".join(user_content)
            })
        
        # Query the base LLM with combined prompts
        response = await super().query(combined_messages, **kwargs)
        return {"content": response.choices[0].message.content if response.choices else ""}
    
    def get_system_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the system prompt for the agent LLM.
        
        Args:
            context: Current execution context for prompt formatting
            query: Current query for prompt formatting
            
        Returns:
            Formatted system prompt if defined, empty string otherwise
        """
        system_prompt = self.agent_prompts.get("system_prompt", "")
        if system_prompt:
            return system_prompt.format(context=context, query=query)
        return ""
    
    def get_user_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the user prompt for the agent LLM.
        
        Args:
            context: Current execution context for prompt formatting
            query: Current query for prompt formatting
            
        Returns:
            Formatted user prompt if defined, empty string otherwise
        """
        user_prompt = self.agent_prompts.get("user_prompt", "")
        if user_prompt:
            return user_prompt.format(context=context, query=query)
        return ""