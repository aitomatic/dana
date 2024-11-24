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
        
        # Format proper LLM request
        llm_request = {
            "prompt": prompt,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', None)
        }
        
        try:
            # Get initial analysis from internal LLM
            llm_response = await self._query_llm(llm_request)
            initial_analysis = llm_response["content"]
            
            # Check if we need expert help
            if "need expert help" in initial_analysis.lower():
                expert_prompt = (
                    f"Please help with this math problem: {query}\n\n"
                    f"My current analysis: {initial_analysis}"
                )
                # Signal that we need to use the math expert resource
                return {
                    "needs_resource": True,
                    "resource_request": {
                        "resource_name": "math_expert",
                        "request": {
                            "prompt": expert_prompt
                        }
                    },
                    "interaction_complete": False
                }
            
            # Parse the response into steps
            steps = self._parse_cot_response(initial_analysis)
            
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
            
            # Check if we need user input
            if "need more information" in initial_analysis.lower():
                return {
                    "needs_user_input": True,
                    "user_prompt": "I need more information. Could you please clarify?",
                    "interaction_complete": False
                }
            
            # If we have a complete solution
            result = {
                "reasoning": initial_analysis,
                "steps": steps,
                "final_answer": steps[-1] if steps else None,
                "interaction_complete": True
            }
            
            # Record the reasoning result
            self.state_manager.add_observation(
                content=result,
                source="reasoning",
                metadata={"type": "reasoning_complete"}
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Reasoning failed: %s", str(e))
            raise

    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the prompt template for Chain of Thought reasoning."""
        # Include any resource responses in the context
        resource_context = ""
        if 'resource_response' in context:
            resource_context = f"\nExpert input: {context['resource_response']}"
            
        return f"""Let's solve this step by step:

Problem: {query}

Context:
{self._format_context(context)}
{resource_context}

Think through this carefully:
1. First, understand what's being asked
2. Break down the problem into parts
3. If you need expert help, say "need expert help"
4. If you need more information, say "need more information"
5. Solve each part systematically
6. Verify your solution

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