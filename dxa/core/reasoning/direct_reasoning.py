"""Direct Reasoning Pattern.

The simplest reasoning pattern that executes tasks directly:

Key Features:
- Single-step execution without complex reasoning
- Direct resource utilization
- Minimal overhead and fast execution

Best For:
- Simple, well-defined tasks
- Tasks with clear execution steps
- When speed is prioritized over explanation

Example:
    ```python
    # The Agent sets up and provides the LLM resource
    agent = Agent("math_agent")
    agent.with_reasoning(DirectReasoning())
    
    # Agent configures the LLM resource internally
    result = await agent.run({
        "primary_resource": "llm",
        "command": "What is 2+2?",
        "system_prompt": "You are a mathematical assistant. Provide numerical answers.",
        "temperature": 0.5
    })

    # Example response:
    {
        "success": True,
        "output": "The sum of 2 and 2 is 4.",
        "insights": {"resource_used": "llm"},
        "confidence": 1.0,
        "reasoning_path": ["execute"]
    }
    ```

Limitations:
- No intermediate reasoning steps
- Limited error recovery
- No complex problem decomposition
"""

from typing import Dict, Any, List
from dxa.core.reasoning.base_reasoning import (
    BaseReasoning, 
    ReasoningResult, 
    ReasoningContext
)

class DirectReasoning(BaseReasoning):
    """Simple direct execution without complex reasoning."""
    
    @property
    def steps(self) -> List[str]:
        """Single execute step."""
        return ["execute"]

    async def _apply_reasoning(self, task: Dict[str, Any], context: ReasoningContext) -> ReasoningResult:
        """Execute task directly."""
        command = task.get('command')
        if not command:
            raise ValueError("Missing command in task")

        # Query LLM with task
        response = await self.agent_llm.query({
            "system": task.get('system_prompt', "Process this task directly and concisely."),
            "user": command,
            "temperature": task.get('temperature', self.config.temperature)
        })

        # Store result in context
        context.history.append({
            "step": "execute",
            "command": command,
            "response": response.get("content")
        })
        
        return ReasoningResult(
            success=True,
            output=response.get("content"),
            insights={"command": command},
            confidence=1.0,
            reasoning_path=self.steps
        )