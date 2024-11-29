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
        """Query the LLM with combined agent and reasoning prompts.
        
        Combines agent-specific prompts with reasoning-specific prompts,
        manages the interaction context, and formats the response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional arguments to pass to the chat completion
            
        Returns:
            Dict containing the processed response content and any additional metadata
            
        Example:
            ```python
            # Agent prompts (set during initialization):
            # system_prompt: "You are an expert in {domain}..."
            # user_prompt: "Analyze: {query}"
            
            # Reasoning provides additional prompts:
            response = await llm.query([
                {"role": "system", "content": "Use step-by-step reasoning..."},
                {"role": "user", "content": "Solve this problem..."}
            ])
            
            # Prompts are combined and response is formatted
            print(response["content"])
            ```
        """
        # Combine agent-specific prompts with provided messages
        combined_messages = []
        
        # Add agent system prompt if it exists
        agent_system = self.get_system_prompt({}, "")
        if agent_system:
            combined_messages.append({"role": "system", "content": agent_system})
        
        # Add provided messages
        combined_messages.extend(messages)
        
        # Add agent user prompt if it exists
        agent_user = self.get_user_prompt({}, "")
        if agent_user:
            # Append to last user message or add new one
            for msg in reversed(combined_messages):
                if msg["role"] == "user":
                    msg["content"] = f"{msg['content']}\n\n{agent_user}"
                    break
            else:
                combined_messages.append({"role": "user", "content": agent_user})
        
        # Query the base LLM with combined prompts
        response = await super().query(combined_messages, **kwargs)
        
        # Format the response
        content = response.choices[0].message.content if response.choices else ""
        return {"content": content}
    
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