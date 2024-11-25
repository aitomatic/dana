"""Chain of Thought reasoning implementation."""

from typing import Dict, Any
from dxa.core.reasoning.base_reasoning import BaseReasoning, ReasoningResult, ReasoningStatus

class ChainOfThoughtReasoning(BaseReasoning):
    """Chain of Thought reasoning pattern."""
    
    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get prompt for Chain of Thought reasoning."""
        return """You are a systematic problem solver that thinks step by step.

Your task is to:
1. Break down problems into steps
2. Show your work clearly
3. Explain your reasoning
4. Ask for help when needed

Always structure your responses like this:

STEPS:
1. [First step explanation]
2. [Second step explanation]
...etc

STATUS: (Choose exactly one)
- NEED_INFO: [Explain what information you need and why]
- COMPLETE: [State your final answer or conclusion]
- ERROR: [Explain what went wrong]"""

    def reason_post_process(self, response: str) -> Dict[str, Any]:
        """Post-process the response from the LLM."""

        # Parse the response
        result = self._parse_response(response)
        return result

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the response from the LLM."""
        reasoning_result = ReasoningResult(
            status=ReasoningStatus.COMPLETE,
            steps=[],
            final_answer=response
        )
        return reasoning_result
