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
    
    async def query(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, str]:
        """Query the LLM with combined agent and reasoning prompts.
        
        Combines agent-specific prompts with reasoning-specific prompts,
        manages the interaction context, and formats the response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional arguments to pass to the chat completion
            
        Returns:
            Dict containing the processed response content
            
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