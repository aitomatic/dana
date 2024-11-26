"""Chain of Thought reasoning implementation."""

from typing import Dict, Any
from dxa.core.reasoning.base_reasoning import BaseReasoning, ReasoningResult, ReasoningStatus

class ChainOfThoughtReasoning(BaseReasoning):
    """Chain of Thought reasoning pattern."""
    
    def get_reasoning_system_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get system prompt for Chain of Thought reasoning."""
        return """You are executing one step in a chain of thought reasoning process.
Always respond in exactly this YAML format:

state: <must be one of>
  - ANALYZE    # Initial analysis of the problem
  - PLAN      # Planning solution steps
  - EXECUTE   # Executing current step
  - VERIFY    # Verifying a result
  - REFLECT   # Evaluating if approach is working
  - BACKTRACK # Need to go back and try different approach
  - AWAIT     # Waiting for resource response
  - DONE      # Solution complete
  - ERROR     # Cannot proceed, explain in error_message

response:
  thought: detailed analysis of current situation
  action: specific action being taken
  result: outcome of the action
  latex: mathematical notation if applicable
  
resource_request:
  needed: true/false
  requests:
    - type: [agent|llm|user|knowledge]
      resource: specific resource name
      purpose: why this resource is needed
      query: specific question or request
      context: relevant context from current solution
  
next:
  state: which state to transition to
  reason: why this state transition is needed
  error_message: required if state is ERROR
  
context:
  previous_states: [list of states we've been through]
  attempted_approaches: [list of approaches tried if any]
  current_approach: description of current solution method
  resource_responses: [previous resource interactions if any]"""

    def get_reasoning_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get prompt for Chain of Thought reasoning."""
        return """Current situation: {situation description}
Previous steps: {summary of previous steps if any}
Current state: {current_state}
Resource responses: {if any resource responses received}
Think about the next step:"""

    def reason_post_process(self, response: str) -> Dict[str, Any]:
        """Post-process the response from the LLM."""

        # Parse the response
        result = self._parse_response(response)
        return result

    def _parse_response(self, response: str) -> ReasoningResult:
        """Parse the structured response from the LLM.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            ReasoningResult containing parsed response
        """
        # Initialize with default values
        steps = []
        status = ReasoningStatus.ERROR  # Default to ERROR
        expert_domain = None
        expert_request = None
        user_prompt = None
        final_answer = None
        explanation = None
        reason = "Failed to parse response"
        suggestion = None
        
        try:
            # Split response into sections
            sections = response.split('\n\n')
            
            # Parse STEPS section
            for section in sections:
                if section.startswith('STEPS:'):
                    steps = [
                        s.strip('123456789. ')
                        for s in section[6:].strip().split('\n')
                        if s.strip()
                    ]
                    
                elif section.startswith('STATUS:'):
                    status_line = section[7:].strip().lower()
                    if 'need_expert:' in status_line:
                        status = ReasoningStatus.NEED_EXPERT
                    elif 'need_info:' in status_line:
                        status = ReasoningStatus.NEED_INFO
                    elif 'complete:' in status_line:
                        status = ReasoningStatus.COMPLETE
                    elif 'error:' in status_line:
                        status = ReasoningStatus.ERROR
                
                elif section.startswith('NEXT_ACTION:'):
                    action = section[12:].strip()
                    for line in action.split('\n'):
                        line = line.strip()
                        if line.startswith('EXPERT:'):
                            expert_domain = line[7:].strip()
                        elif line.startswith('QUERY:'):
                            if status == ReasoningStatus.NEED_EXPERT:
                                expert_request = {
                                    "domain": expert_domain,
                                    "request": {"prompt": line[6:].strip()}
                                }
                            else:
                                user_prompt = line[6:].strip()
                        elif line.startswith('FINAL_ANSWER:'):
                            final_answer = line[13:].strip()
                        elif line.startswith('EXPLANATION:'):
                            explanation = line[12:].strip()
                        elif line.startswith('REASON:'):
                            reason = line[7:].strip()
                        elif line.startswith('SUGGESTION:'):
                            suggestion = line[11:].strip()
            
            # If no steps were found but we have content
            if not steps and response.strip():
                steps = [response.strip()]
            
            # Validate parsed result
            if status == ReasoningStatus.COMPLETE and not final_answer:
                status = ReasoningStatus.ERROR
                reason = "No final answer provided"
            elif status == ReasoningStatus.NEED_EXPERT and not expert_request:
                status = ReasoningStatus.ERROR
                reason = "No expert request provided"
            elif status == ReasoningStatus.NEED_INFO and not user_prompt:
                status = ReasoningStatus.ERROR
                reason = "No user prompt provided"
            
        except Exception as e:
            self.logger.error("Failed to parse LLM response: %s", str(e))
            steps = [str(e)]
            status = ReasoningStatus.ERROR
            reason = f"Failed to parse response: {str(e)}"
        
        return ReasoningResult(
            status=status,
            steps=steps,
            expert_domain=expert_domain,
            expert_request=expert_request,
            user_prompt=user_prompt,
            final_answer=final_answer,
            explanation=explanation,
            reason=reason,
            suggestion=suggestion
        )
