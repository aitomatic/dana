"""Chain of Thought reasoning implementation.

This module implements the Chain of Thought (CoT) reasoning pattern, which:
- Breaks down complex problems into logical steps
- Shows explicit reasoning for each step
- Maintains transparency in decision-making
- Enables verification of reasoning process

The CoT approach helps agents explain their thinking and validate their
conclusions through step-by-step analysis.

Classes:
    ChainOfThoughtReasoning: Implementation of Chain of Thought reasoning

Example:
    >>> reasoning = ChainOfThoughtReasoning()
    >>> result = await reasoning.reason(
    ...     context={"problem": "complex math equation"},
    ...     query="Solve x^2 + 2x + 1 = 0"
    ... )
"""

from typing import Dict, Any, Optional
from dxa.core.reasoning.base_reasoning import BaseReasoning, ReasoningConfig

class ChainOfThoughtReasoning(BaseReasoning):
    """Chain of Thought reasoning pattern."""
    
    def __init__(self, config: Optional[ReasoningConfig] = None):
        """Initialize Chain of Thought reasoning."""
        super().__init__(config=config)
    
    async def initialize(self) -> None:
        """Initialize reasoning system."""
        if self.agent_llm:
            await self.agent_llm.initialize()
    
    async def cleanup(self) -> None:
        """Clean up reasoning system."""
        if self.agent_llm:
            await self.agent_llm.cleanup()
    
    async def reason(self, context: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Run reasoning cycle."""
        # Get prompts
        system_prompt = self.get_system_prompt(context, query)
        user_prompt = self.get_prompt(context, query)
        llm_config = self.config.llm_config;
        
        # Query LLM
        response = await self._query_agent_llm({
            "system_prompt": system_prompt,
            "prompt": user_prompt,
            "temperature": llm_config["temperature"],
            "max_tokens": llm_config["max_tokens"]
        })
        
        # Process response
        return self.reason_post_process(response.choices[0].message.content)
    
    def get_reasoning_system_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get system prompt for Chain of Thought reasoning."""
        return """You are executing one step in a chain of thought reasoning process.
        Always show your work step by step."""

    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get prompt for Chain of Thought reasoning."""
        return f"""Let's solve this step by step:
        Query: {query}
        Context: {context}
        
        1. First, let's understand what we're trying to do
        2. Then, break down the problem into steps
        3. Finally, solve each step methodically
        
        Please show your reasoning for each step."""

    def reason_post_process(self, response: str) -> Dict[str, Any]:
        """Process the chain of thought response."""
        return {
            "response": response,
            "reasoning_type": "chain_of_thought"
        }
