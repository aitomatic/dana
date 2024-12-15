"""Chain of Thought (CoT) Reasoning Pattern.

A step-by-step reasoning approach that breaks down complex problems:

Key Features:
- Explicit reasoning steps: understand → analyze → solve → verify
- Maintains clear thought process
- Built-in solution verification
- Detailed explanations at each step

Best For:
- Complex problem-solving
- Educational explanations
- When reasoning transparency is important
- Tasks requiring step-by-step breakdown

Example:
    ```python
    reasoning = ChainOfThoughtReasoning()
    result = await reasoning.execute(
        task={"objective": "Solve this math problem..."},
        context=context
    )
    ```

Steps:
1. Understand: Identify core problem and requirements
2. Analyze: Break down into sub-problems
3. Solve: Apply solution step-by-step
4. Verify: Validate solution against requirements
"""

from typing import Dict, Any, List, Optional
from dxa.core.reasoning.base_reasoning import (
    BaseReasoning, 
    ReasoningResult, 
    ReasoningContext,
    StepResult,
    ReasoningStatus
)

class ChainOfThoughtReasoning(BaseReasoning):
    """Step by step reasoning with explicit thought process."""
    
    @property
    def steps(self) -> List[str]:
        return ["understand", "analyze", "solve", "verify"]
    
    def get_initial_step(self) -> str:
        return "understand"

    async def _core_execute(self, 
                          task: Dict[str, Any],
                          context: ReasoningContext) -> ReasoningResult:
        await self._init_objective(context)
        current_step = self.get_initial_step()
        
        while current_step:
            # Get prompt for current step
            prompt = self.get_step_prompt(current_step, context, task, self.previous_steps)
            
            # Execute step
            response = await self._query_agent_llm({
                "prompt": prompt,
                "system_prompt": f"You are executing the {current_step} step."
            })
            
            # Process step result
            step_result = self._process_step(current_step, response["response"])
            
            # Store step result
            self.previous_steps.append({
                "step": current_step,
                "result": step_result
            })
            
            # Move to next step or finish
            if step_result.status != ReasoningStatus.COMPLETE:
                return ReasoningResult(
                    success=False,
                    output=step_result.content,
                    insights={"failed_step": current_step},
                    confidence=0.0,
                    reasoning_path=self._get_reasoning_path()
                )
                
            current_step = self.get_next_step(current_step, step_result)
        
        # Get final result from verify step
        final_result = self.previous_steps[-1]["result"]
        return ReasoningResult(
            success=True,
            output=final_result.content,
            insights={
                "steps": self.previous_steps,
                "objective": self.objective_state.current,
                "objective_evolution": self.objective_state.refinements
            },
            confidence=final_result.confidence if hasattr(final_result, 'confidence') else 1.0,
            reasoning_path=self._get_reasoning_path()
        )

    def get_step_prompt(self,
                       step: str,
                       context: Dict[str, Any],
                       task: Dict[str, Any],
                       previous_steps: List[Dict[str, Any]]) -> str:
        """Get prompt for specific step."""
        prompts = {
            "understand": self._get_understand_prompt,
            "analyze": self._get_analyze_prompt,
            "solve": self._get_solve_prompt,
            "verify": self._get_verify_prompt
        }
        return prompts[step](context, task, previous_steps)

    def get_next_step(self, current_step: str, step_result: StepResult) -> Optional[str]:
        """Get next step in sequence."""
        step_order = self.steps
        try:
            current_index = step_order.index(current_step)
            return step_order[current_index + 1] if current_index < len(step_order) - 1 else None
        except ValueError:
            return None

    def _get_understand_prompt(self, context: Dict[str, Any], task: Dict[str, Any], previous_steps: List[Dict[str, Any]]) -> str:
        return f"""
        Objective: {context.objective}
        Task: {task.get('command')}
        
        Let's understand what we're being asked:
        1. What is the core question/problem?
        2. What are the key pieces of information provided?
        3. What are we expected to deliver?
        4. Are there any implicit requirements or constraints?
        
        Think step by step and be explicit about your understanding.
        """

    def _get_analyze_prompt(self, context: Dict[str, Any], task: Dict[str, Any], previous_steps: List[Dict[str, Any]]) -> str:
        understanding = self._format_previous_step(previous_steps, "understand")
        return f"""
        Understanding: {understanding}
        
        Let's analyze how to solve this:
        1. What are the key components or sub-problems?
        2. What approaches could we use?
        3. What assumptions are we making?
        4. What resources will we need?
        
        Break down your analysis step by step.
        """

    def _get_solve_prompt(self, context: Dict[str, Any], task: Dict[str, Any], previous_steps: List[Dict[str, Any]]) -> str:
        understanding = self._format_previous_step(previous_steps, "understand")
        analysis = self._format_previous_step(previous_steps, "analyze")
        return f"""
        Understanding: {understanding}
        Analysis: {analysis}
        
        Let's solve this step by step:
        1. Follow the approach identified in analysis
        2. Show your work at each step
        3. Explain your reasoning
        4. Note any intermediate results
        
        Be explicit about each step in your solution process.
        """

    def _get_verify_prompt(self, context: Dict[str, Any], task: Dict[str, Any], previous_steps: List[Dict[str, Any]]) -> str:
        understanding = self._format_previous_step(previous_steps, "understand")
        solution = self._format_previous_step(previous_steps, "solve")
        return f"""
        Original Objective: {context.objective}
        Understanding: {understanding}
        Solution: {solution}
        
        Let's verify our solution:
        1. Does it fully answer the original question?
        2. Have we met all requirements (explicit and implicit)?
        3. Are our calculations and logic correct?
        4. What are the limitations or edge cases?
        
        Be thorough in your verification and note any concerns.
        """

    def _process_step(self, step: str, response: str) -> StepResult:
        """Process raw response into step result."""
        return StepResult(
            status=ReasoningStatus.COMPLETE,
            content=response
        )

    def _get_reasoning_path(self) -> List[str]:
        """Get the path taken through reasoning steps."""
        return [step["step"] for step in self.previous_steps]
