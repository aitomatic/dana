"""Chain of Thought reasoning implementation."""

from typing import Dict, Any, List
from dxa.core.reasoning.base import BaseReasoning
from dxa.core.state import StateManager

class ChainOfThoughtReasoning(BaseReasoning):
    """Chain of Thought reasoning pattern."""
    
    def __init__(self):
        """Initialize Chain of Thought reasoning."""
        super().__init__()
        self.state_manager = StateManager()

    async def reason(
        self,
        context: Dict[str, Any],
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute Chain of Thought reasoning process."""
        # Record the start of reasoning
        self.state_manager.add_observation(
            content=query,
            source="query",
            metadata={"type": "reasoning_start"}
        )
        
        # Build the CoT prompt
        prompt = self.get_reasoning_prompt(context, query)
        
        # Get response from LLM using parent class method
        response = await super()._query_llm(prompt)
        
        # Parse the response into steps
        steps = self._parse_cot_response(response)
        
        # Record each reasoning step
        for i, step in enumerate(steps):
            self.state_manager.add_observation(
                content=step,
                source="reasoning",
                metadata={
                    "type": "reasoning_step",
                    "step_number": i + 1
                }
            )
        
        result = {
            "reasoning": response,
            "steps": steps,
            "final_answer": steps[-1] if steps else None
        }
        
        # Record the reasoning result
        self.state_manager.add_observation(
            content=result,
            source="reasoning",
            metadata={"type": "reasoning_complete"}
        )
        
        return result

    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the prompt template for Chain of Thought reasoning."""
        # Get recent observations for context
        recent_obs = self.state_manager.get_recent_observations()
        obs_context = "\n".join(
            f"Previous observation: {obs.content}"
            for obs in recent_obs
        )
        
        return f"""Let's solve this step by step:

Problem: {query}

Context:
{self._format_context(context)}

Previous observations:
{obs_context}

Think through this carefully:
1. First, understand what's being asked
2. Break down the problem into parts
3. Solve each part systematically
4. Verify your solution

Show your complete reasoning process."""

    def _parse_cot_response(self, response: str) -> List[str]:
        """Parse the response into reasoning steps."""
        steps = []
        current_step = []
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a new step marker
            if line[0].isdigit() and '.' in line[:3]:
                if current_step:
                    steps.append(' '.join(current_step))
                    current_step = []
                current_step.append(line)
            else:
                current_step.append(line)
                
        # Add the last step
        if current_step:
            steps.append(' '.join(current_step))
            
        return steps

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for inclusion in prompts."""
        formatted = []
        for key, value in context.items():
            if isinstance(value, dict):
                formatted.append(f"{key}:")
                for k, v in value.items():
                    formatted.append(f"  {k}: {v}")
            elif isinstance(value, (list, tuple)):
                formatted.append(f"{key}:")
                for item in value:
                    formatted.append(f"  - {item}")
            else:
                formatted.append(f"{key}: {value}")
        return '\n'.join(formatted)

    async def initialize(self) -> None:
        """Initialize the reasoning pattern."""
        self.state_manager = StateManager()
        self.logger.info("Chain of Thought reasoning initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.state_manager.clear_history()
        self.logger.info("Chain of Thought reasoning cleaned up")