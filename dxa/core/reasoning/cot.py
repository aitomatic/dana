"""Chain of Thought reasoning implementation."""

from typing import Dict, Any
from dxa.core.reasoning.base_reasoning import BaseReasoning, ReasoningResult, ReasoningStatus

class ChainOfThoughtReasoning(BaseReasoning):
    """Chain of Thought reasoning pattern."""

    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get prompt for Chain of Thought reasoning."""
        formatted_context = "\n".join([f"{key}: {value}" for key, value in context.items()])
        prompt = (
            "You are a systematic problem solver that thinks step by step.\n"
            "\n"
            "Your task is to:\n"
            "1. Break down problems into steps\n"
            "2. Show your work clearly\n"
            "3. Explain your reasoning\n"
            "4. Ask for help when needed\n"
            "\n"
            "Always structure your responses like this:\n"
            "\n"
            "STEPS:\n"
            "1. [First step explanation]\n"
            "2. [Second step explanation]\n"
            "...etc\n"
            "\n"
            "STATUS: (Choose exactly one)\n"
            "- NEED_INFO: [Explain what information you need and why]\n"
            "- NEED_EXPERT: [Explain what information you need help from expert and why]\n"
            "- COMPLETE: [State your final answer or conclusion]\n"
            "- ERROR: [Explain what went wrong]\n"
            "\n"
            f"CONTEXT:\n{formatted_context}\n"
            f"PROBLEM: {query}"
        )
        return prompt

    def reason_post_process(self, response: str) -> Dict[str, Any]:
        """Post-process the response from the LLM."""
        # Parse the response
        result = self._parse_response(response)
        return result

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the response from the LLM."""
        # Extract the status from the response
        status_line = [line for line in response.splitlines() if line.startswith("STATUS:")][0]
        status = status_line.split(":")[1].strip()

        reasoning_result = ReasoningResult(
            status=status,  # Use the extracted status
            steps=[],
            final_answer=response
        )
        return reasoning_result
