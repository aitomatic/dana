"""Chain of Thought (CoT) Reasoning Pattern

Chain of Thought is a reasoning paradigm that enhances LLM problem-solving by:
1. Breaking down complex problems into explicit reasoning steps
2. Maintaining a clear thought process throughout the solution
3. Enabling verification and correction of reasoning

How CoT Works:
-------------
CoT guides the LLM through four key phases:

1. UNDERSTAND:
   - Identifies the core question/problem
   - Extracts key information
   - Clarifies expected outcomes
   
2. ANALYZE:
   - Breaks down into sub-problems
   - Identifies solution approaches
   - States key assumptions

3. SOLVE:
   - Applies chosen methods step-by-step
   - Shows intermediate work
   - Explains reasoning at each step

4. VERIFY:
   - Validates against original question
   - Checks logic and calculations
   - Considers edge cases
   - Presents final verified answer

Implementation in DXA:
--------------------
The ChainOfThoughtReasoning class implements CoT by:

1. Extending BaseReasoning:
   ```python
   class ChainOfThoughtReasoning(BaseReasoning):
       @property
       def steps(self) -> List[str]:
           return ["understand", "analyze", "solve", "verify"]
   ```

2. Providing Step-Specific Prompts:
   - Each step has a dedicated prompt generator
   - Prompts include previous step results for context
   - Clear instructions guide the LLM's focus

3. Linear Progression:
   - Steps execute in sequence
   - Each step builds on previous results
   - Process stops if resource needed or error occurs

4. Verification Focus:
   - Final step dedicated to solution verification
   - Checks completeness and correctness
   - Considers limitations and edge cases

Usage Example:
------------
```python
reasoning = ChainOfThoughtReasoning()
result = await reasoning.reason(
    context={"relevant_data": "..."}, 
    query="Solve this problem..."
)
```

Benefits:
--------
- Transparent Reasoning: Each step's logic is explicit
- Structured Approach: Consistent problem-solving pattern
- Verifiable Results: Built-in solution checking
- Error Recovery: Can request resources when needed

The CoT pattern is particularly effective for:
- Complex problem-solving
- Mathematical reasoning
- Step-by-step explanations
- Teaching and demonstration
"""

from typing import Dict, Any, List, Optional
from dxa.core.reasoning.base_reasoning import BaseReasoning, StepResult, ReasoningStatus

class ChainOfThoughtReasoning(BaseReasoning):
    """Chain of Thought reasoning pattern."""
    
    @property
    def steps(self) -> List[str]:
        """Get list of possible steps."""
        return ["understand", "analyze", "solve", "verify"]
    
    def get_initial_step(self) -> str:
        """Get the initial step for reasoning."""
        return "understand"

    def get_step_prompt(self,
                        step: str,
                        context: Dict[str, Any],
                        query: str,
                        previous_steps: List[Dict[str, Any]]) -> str:
        """Get the prompt for a specific step."""
        prompts = {
            "understand": self._get_understand_prompt,
            "analyze": self._get_analyze_prompt,
            "solve": self._get_solve_prompt,
            "verify": self._get_verify_prompt
        }
        return prompts[step](context, query, previous_steps)

    def get_next_step(self, current_step: str, step_result: StepResult) -> Optional[str]:
        """Determine the next step based on current step and its result."""
        # If we need resources or have error/completion, stop here
        if step_result.status != ReasoningStatus.COMPLETE:
            return None
            
        # Move to next step in sequence, stop at end
        step_order = self.steps
        current_index = step_order.index(current_step)
        if current_index < len(step_order) - 1:
            return step_order[current_index + 1]
        return None

    def get_reasoning_system_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the reasoning system prompt."""
        return f"""You are executing the {self.current_step} step in a chain-of-thought reasoning process.
        Show your work step by step and explain your thinking clearly."""

    def reason_post_process(self, response: str) -> StepResult:
        """Process the response from the LLM."""
        # Basic implementation - could be enhanced with more sophisticated parsing
        return StepResult(
            status=ReasoningStatus.COMPLETE,
            content=response,
            final_answer=response if self.current_step == "verify" else None
        )

    # pylint: disable=unused-argument
    def _get_understand_prompt(self, context: Dict[str, Any], query: str, previous_steps: List[Dict[str, Any]]) -> str:
        """Get prompt for understanding step.
        
        Args:
            context: The reasoning context
            query: The user query
            previous_steps: Results from previous steps
            
        Returns:
            str: The formatted prompt for the understand step
        """
        return f"""UNDERSTAND step:
        Query: {query}
        Context: {self._format_context(context)}
        
        Let's understand what we're being asked:
        1. What is the core question or problem?
        2. What are the key pieces of information provided?
        3. What are the expected outcomes or deliverables?"""

    def _get_analyze_prompt(self, context: Dict[str, Any], query: str, previous_steps: List[Dict[str, Any]]) -> str:
        """Get prompt for analysis step.
        
        Args:
            context: The reasoning context                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
            query: The user query
            previous_steps: Results from previous steps
            
        Returns:
            str: The formatted prompt for the analyze step
        """
        return f"""ANALYZE step:
        Query: {query}
        Context: {self._format_context(context)}
        Understanding: {self._format_previous_step(previous_steps, "understand")}
        
        Let's break down the problem:
        1. What are the key components or sub-problems?
        2. What methods or approaches could we use?
        3. What assumptions do we need to make?"""

    def _get_solve_prompt(self, context: Dict[str, Any], query: str, previous_steps: List[Dict[str, Any]]) -> str:
        """Get prompt for solution step.
        
        Args:
            context: The reasoning context
            query: The user query
            previous_steps: Results from previous steps
            
        Returns:
            str: The formatted prompt for the solve step
        """
        return f"""SOLVE step:
        Query: {query}
        Context: {self._format_context(context)}
        Analysis: {self._format_previous_step(previous_steps, "analyze")}
        
        Let's solve the problem:
        1. Apply the chosen method step by step
        2. Show all work and intermediate results
        3. Explain each step of the solution"""

    def _get_verify_prompt(self, context: Dict[str, Any], query: str, previous_steps: List[Dict[str, Any]]) -> str:
        """Get prompt for verification step.
        
        Args:
            context: The reasoning context
            query: The user query
            previous_steps: Results from previous steps
            
        Returns:
            str: The formatted prompt for the verify step
        """
        return f"""VERIFY step:
        Query: {query}
        Context: {self._format_context(context)}
        Solution: {self._format_previous_step(previous_steps, "solve")}
        
        Let's verify our solution:
        1. Check if the solution answers the original question
        2. Verify the logic and calculations
        3. Consider edge cases or limitations
        4. Provide the final, verified answer"""
