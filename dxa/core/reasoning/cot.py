"""Chain of Thought reasoning implementation."""

from typing import Dict, Any
from dxa.core.reasoning.base_reasoning import BaseReasoning

class ChainOfThoughtReasoning(BaseReasoning):
    """Chain of Thought reasoning pattern."""
    
    def __init__(self):
        """Initialize Chain of Thought reasoning."""
        super().__init__()
    
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
        
        # Query LLM
        response = await self._query_agent_llm({
            "system_prompt": system_prompt,
            "prompt": user_prompt,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        })
        
        # Process response
        return self.reason_post_process(response["content"])
    
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
