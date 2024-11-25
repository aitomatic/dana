"""Chain of Thought reasoning implementation."""

from typing import Dict, Any
from dxa.core.reasoning.base_reasoning import BaseReasoning, ReasoningStatus, ReasoningResult
from dxa.agents.state import StateManager
from dxa.core.common.exceptions import ReasoningError, ParseError, LLMError

class ChainOfThoughtReasoning(BaseReasoning):
    """Chain of Thought reasoning pattern."""
    
    def __init__(self):
        """Initialize Chain of Thought reasoning."""
        super().__init__()
        self.available_experts = []
        self.llm = None  # This should be set during initialization

    def has_expert_for(self, domain: str) -> bool:
        """Check if an expert is available for the given domain."""
        return domain in self.available_experts

    def get_system_prompt(self) -> str:
        """Get system prompt for Chain of Thought reasoning."""
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
- ERROR: [Explain what went wrong]

NEXT_ACTION: (Based on STATUS)
If NEED_INFO:
  QUERY: [specific question for the user]
  CONTEXT: [why you need this information]
  FORMAT: [expected format of the answer]
If COMPLETE:
  FINAL_ANSWER: [the solution or conclusion]
  EXPLANATION: [why this is the answer]
If ERROR:
  REASON: [error explanation]
  SUGGESTION: [how to proceed]"""

    def get_reasoning_prompt(self, context: Dict[str, Any], task_spec: str) -> str:
        """Get the prompt template for Chain of Thought reasoning."""
        # Start with the task specification
        prompt_parts = [
            "Let's solve this step by step:",
            f"\nTask: {task_spec}"
        ]
        
        # Add any user input if available
        if 'user_input' in context:
            prompt_parts.append(f"\nAdditional Information: {context['user_input']}")
        
        # Add any expert response if available
        if 'expert_response' in context:
            prompt_parts.append(
                f"\nExpert Input: {context['expert_response'].get('content', '')}"
            )
        
        # Add any other context
        other_context = {
            k: v for k, v in context.items()
            if k not in {'task_spec', 'user_input', 'expert_response'}
        }
        if other_context:
            prompt_parts.append("\nContext:")
            prompt_parts.extend(self._format_context(other_context).split('\n'))
        
        prompt_parts.append("\nThink through this carefully and show your complete reasoning process.")
        
        return "\n".join(prompt_parts)

    async def reason(
        self,
        context: Dict[str, Any],
        query: str,
        **kwargs
    ) -> ReasoningResult:
        """Execute Chain of Thought reasoning process.
        
        Args:
            context: Current context including:
                - task_spec: The problem/task specification
                - user_input: Any user provided information
                - expert_response: Any expert provided information
            query: The problem/task specification
            **kwargs: Additional arguments
            
        Returns:
            ReasoningResult containing next action to take
        """
        # Record the start of reasoning
        self.state_manager.add_observation(
            content={"task_spec": query, "context": context},
            source="reasoning",
            metadata={"type": "reasoning_start"}
        )
        
        # Build the CoT prompt
        prompt = self.get_reasoning_prompt(context, query)
        
        # Format proper LLM request with system prompt
        agent_llm_request = {
            "messages": [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', None)
        }
        
        try:
            # Get response from LLM
            try:
                agent_llm_response = await self._query_llm(agent_llm_request)
            except LLMError as e:
                raise ReasoningError(f"LLM query failed: {str(e)}") from e
            
            # Parse the structured response
            try:
                content = agent_llm_response.choices[0].message.content
                result = self._parse_response(content)
            except ParseError as e:
                raise ReasoningError(f"Failed to parse LLM response: {str(e)}") from e
            
            # Record the reasoning result
            self.state_manager.add_observation(
                content={"result": result},
                source="reasoning",
                metadata={"type": "reasoning_complete"}
            )
            
            return result
            
        except ReasoningError:
            raise
        except Exception as e:
            raise ReasoningError(f"Unexpected error in reasoning: {str(e)}") from e

    def _parse_response(self, response: str) -> ReasoningResult:
        """Parse the structured response."""
        steps = []
        status = ReasoningStatus.ERROR  # Default to ERROR
        expert_domain = None
        expert_request = None
        expert_context = None
        user_prompt = None
        user_context = None
        expected_format = None
        final_answer = None
        explanation = None
        reason = "Failed to parse response"  # Default error reason
        suggestion = None
        
        try:
            # Parse sections
            sections = response.split('\n\n')
            for section in sections:
                section = section.strip().lower()  # Convert to lowercase for comparison
                try:
                    if section.startswith('steps:'):
                        steps = [
                            s.strip('123456789. ')
                            for s in section[6:].strip().split('\n')
                            if s.strip()
                        ]
                    
                    elif section.startswith('status:'):
                        status_line = section[7:].strip()
                        if 'need_expert' in status_line:
                            status = ReasoningStatus.NEED_EXPERT
                        elif 'need_info' in status_line:
                            status = ReasoningStatus.NEED_INFO
                        elif 'complete' in status_line:
                            status = ReasoningStatus.COMPLETE
                        elif 'error' in status_line:
                            status = ReasoningStatus.ERROR
                    
                    elif section.startswith('next_action:'):
                        action = section[12:].strip()
                        for line in action.split('\n'):
                            line = line.strip().lower()  # Convert to lowercase for comparison
                            if line.startswith('expert:'):
                                expert_domain = line[7:].strip()
                            elif line.startswith('query:'):
                                if status == ReasoningStatus.NEED_EXPERT:
                                    expert_request = {
                                        "domain": expert_domain,
                                        "request": {"prompt": line[6:].strip()}
                                    }
                                else:
                                    user_prompt = line[6:].strip()
                            elif line.startswith('context:'):
                                if status == ReasoningStatus.NEED_EXPERT:
                                    expert_context = line[8:].strip()
                                else:
                                    user_context = line[8:].strip()
                            elif line.startswith('format:'):
                                expected_format = line[7:].strip()
                            elif line.startswith('final_answer:'):
                                final_answer = line[13:].strip()
                            elif line.startswith('explanation:'):
                                explanation = line[12:].strip()
                            elif line.startswith('reason:'):
                                reason = line[7:].strip()
                            elif line.startswith('suggestion:'):
                                suggestion = line[11:].strip()

                except (AttributeError, IndexError) as e:
                    raise ParseError(f"Failed to parse section: {str(e)}") from e
            
            # Validate the parsed result
            if not steps:
                reason = "No reasoning steps provided"
            elif status == ReasoningStatus.NEED_EXPERT and not expert_request:
                reason = "Expert request missing required fields"
            elif status == ReasoningStatus.NEED_INFO and not user_prompt:
                reason = "User prompt missing"
            elif status == ReasoningStatus.COMPLETE and not final_answer:
                reason = "Final answer missing"
            
        except (ValueError, KeyError) as e:
            raise ParseError(f"Failed to parse response: {str(e)}") from e
        
        return ReasoningResult(
            status=status,
            steps=steps,
            expert_domain=expert_domain,
            expert_request=expert_request,
            expert_context=expert_context,
            user_prompt=user_prompt,
            user_context=user_context,
            expected_format=expected_format,
            final_answer=final_answer,
            explanation=explanation,
            reason=reason,
            suggestion=suggestion,
            raw_content=response  # Store the entire original response
        )

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
        self.state_manager = StateManager(agent_name="chain_of_thought")
        self.logger.info("Chain of Thought reasoning initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.state_manager.clear_history()
        self.logger.info("Chain of Thought reasoning cleaned up")
