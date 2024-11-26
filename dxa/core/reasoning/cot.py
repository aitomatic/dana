"""Chain of Thought reasoning implementation."""

from typing import Dict, Any
from dxa.core.reasoning.base_reasoning import BaseReasoning, ReasoningResult, ReasoningStatus

class ChainOfThoughtReasoning(BaseReasoning):
    """Chain of Thought reasoning pattern."""

    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get prompt for Chain of Thought reasoning."""
        status_dict = {
            'NEED_INFO': '[Explain what information you need and why]',
            'NEED_EXPERT': '[Explain what information you need to ask expert domain and why]',
            'COMPLETE': '[State your final answer or conclusion]',
            'ERROR': '[Explain what went wrong]'
        }
        status_names = '['
        status_explaination = ''
        for key, value in status_dict.items():
            status_names += key
            status_names += ','
            status_explaination += f" - In the case status {key}: {value}\n"
        if status_names[-1] == ',':
            status_names = status_names[:-1]
        status_names += ']'

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
            "Always structure your responses like this (case sensitive):\n"
            "\n"
            "STEPS:\n"
            "1. [First step explanation]\n"
            "2. [Second step explanation]\n"
            "...etc\n"
            "\n"
            f"STATUS: (Choose exactly one in following list: {status_names})\n"
            "\n"
            f"STATUS_EXPLANATION:{status_explaination}"
            "\n"
            "'EXPERT_DOMAIN: (Choose expert domains in resources of the context that requires for the qroblem. "
            "Answer exactly values in the resources. Answer the 'NONE' if not match any expert domains in the resources)"
            "\n"
            "--------------------------------------"
            "\n"
            "--------------------------------------"
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
        status_line = [line for line in response.splitlines() if line.startswith("STATUS:")]
        if not status_line:
            raise ValueError("STATUS line not found in response.")
        status_line = status_line[0]
        
        status_data = status_line.split(":")
        status_line = status_data[1].strip()
        if ' - ' in status_line:
            status = status_line.split(" - ")[1].strip()
        else:
            status = status_line

        expert_domain_line = [line for line in response.splitlines() if line.startswith("EXPERT_DOMAIN:")]
        if not expert_domain_line:
            raise ValueError("EXPERT_DOMAIN line not found in response.")
        expert_domain_line = expert_domain_line[0]
        
        expert_domain = None 
        response_expert_domain = expert_domain_line.split(":")[1].strip()
        if response_expert_domain != 'NONE':
            expert_domain = response_expert_domain
        
        explain_line = [line for line in response.splitlines() if line.startswith("STATUS_EXPLANATION:")]
        if not explain_line:
            raise ValueError("STATUS_EXPLANATION line not found in response.")
        explain_line = explain_line[0]
        
        status_explaination = explain_line.split(":")[1].strip()
        user_prompt = None
        expert_request = None
        explaination = None
        if status == 'NEED_INFO':
            user_prompt = status_explaination
        elif status == 'NEED_EXPERT':
            expert_request = status_explaination
        elif status == 'COMPLETE':
            explaination = status_explaination

        reasoning_result = ReasoningResult(
            status=status,  # Use the extracted status
            steps=[],
            final_answer=response,
            expert_domain=expert_domain,
            user_prompt=user_prompt,
            expert_request=expert_request,
            explanation=explaination
        )
        return reasoning_result
