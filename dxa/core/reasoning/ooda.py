"""OODA (Observe, Orient, Decide, Act) Loop Reasoning Pattern

The OODA loop is a decision-making framework originally developed by military 
strategist John Boyd. In DXA, it provides a dynamic reasoning approach that 
continuously adapts to changing situations.

How OODA Works:
-------------
The OODA loop cycles through four interconnected phases:

1. OBSERVE:
   - Gathers raw information and data
   - Identifies key data points and patterns
   - Monitors changes in the situation
   - Collects unfiltered inputs

2. ORIENT:
   - Analyzes gathered information
   - Applies context and experience
   - Forms mental models
   - Considers cultural traditions, genetic heritage, and previous experiences
   - Synthesizes information into understanding

3. DECIDE:
   - Evaluates possible courses of action
   - Considers hypotheses about situation
   - Selects most appropriate action
   - Makes decisions based on oriented understanding

4. ACT:
   - Implements the chosen decision
   - Tests hypotheses in real world
   - Generates new observations
   - Feeds back into the OODA cycle

Implementation in DXA:
--------------------
The OODAReasoning class implements this cycle by:

1. Continuous Adaptation:
   ```python
   @property
   def steps(self) -> List[str]:
       return ["observe", "orient", "decide", "act"]
   ```
   - Each step feeds into the next
   - Cycle can repeat as needed
   - Maintains situational awareness

2. Dynamic Feedback:
   - Each phase informs the others
   - Results feed back into observation
   - Allows for rapid adaptation
   - Handles changing circumstances

3. Resource Integration:
   - Can pull in expert knowledge
   - Utilizes human feedback
   - Accesses tools and data
   - Adapts to available resources

4. Practical Application:
   - Problem analysis
   - Decision making
   - Strategy development
   - Continuous improvement

Usage Example:
------------
```python
reasoning = OODAReasoning()
result = await reasoning.reason(
    context={"situation_data": "..."}, 
    query="What action should we take?"
)
```

Benefits:
--------
- Adaptive: Continuously updates understanding
- Dynamic: Responds to changing conditions
- Practical: Focuses on actionable decisions
- Iterative: Learns from results

The OODA pattern excels in:
- Strategic planning
- Real-time decision making
- Competitive situations
- Adaptive problem solving
- Continuous improvement cycles

Key Differences from Other Patterns:
---------------------------------
Unlike linear reasoning patterns, OODA:
- Is inherently cyclical
- Emphasizes rapid adaptation
- Focuses on situational awareness
- Integrates feedback continuously
"""

from typing import Dict, Any, List, Optional
from dxa.core.reasoning.base_reasoning import BaseReasoning, StepResult, ReasoningStatus

class OODAReasoning(BaseReasoning):
    """OODA loop reasoning implementation."""
    
    @property
    def steps(self) -> List[str]:
        """Get list of possible steps."""
        return ["observe", "orient", "decide", "act"]
    
    def get_initial_step(self) -> str:
        """Get the initial step for reasoning."""
        return "observe"

    def get_step_prompt(self,
                        step: str,
                        context: Dict[str, Any],
                        query: str,
                        previous_steps: List[Dict[str, Any]]) -> str:
        """Get the prompt for a specific step."""
        prompts = {
            "observe": self._get_observe_prompt,
            "orient": self._get_orient_prompt,
            "decide": self._get_decide_prompt,
            "act": self._get_act_prompt
        }
        return prompts[step](context, query, previous_steps)

    def get_next_step(self, current_step: str, step_result: StepResult) -> Optional[str]:
        """Determine the next step based on current step and its result."""
        # If we need resources or have error/completion, stop here
        if step_result.status != ReasoningStatus.COMPLETE:
            return None
            
        # Otherwise continue OODA cycle
        step_order = self.steps
        current_index = step_order.index(current_step)
        return step_order[(current_index + 1) % len(step_order)]

    def get_reasoning_system_prompt(self, context: Dict[str, Any], query: str) -> str:
        """Get the reasoning system prompt."""
        return f"""You are executing the {self.current_step} phase in an OODA loop reasoning process.
        Consider both immediate observations and long-term patterns."""

    def reason_post_process(self, response: str) -> StepResult:
        """Process the response from the LLM."""
        # Basic implementation - could be enhanced with more sophisticated parsing
        return StepResult(
            status=ReasoningStatus.COMPLETE,
            content=response
        )

    # pylint: disable=unused-argument
    def _get_observe_prompt(self, context: Dict[str, Any], query: str, previous_steps: List[Dict[str, Any]]) -> str:
        """Get prompt for observation phase.
        
        Args:
            context: The reasoning context
            query: The user query
            previous_steps: Results from previous steps
            
        Returns:
            str: The formatted prompt for the observe phase
        """
        return f"""OBSERVE phase:
        Query: {query}
        Context: {self._format_context(context)}
        
        What are the key observations about this situation?
        Consider:
        1. What information do we have?
        2. What information might we need?
        3. What patterns or anomalies do we notice?"""

    def _get_orient_prompt(self, context: Dict[str, Any], query: str, previous_steps: List[Dict[str, Any]]) -> str:
        """Get prompt for orientation phase.
        
        Args:
            context: The reasoning context
            query: The user query
            previous_steps: Results from previous steps
            
        Returns:
            str: The formatted prompt for the orient phase
        """
        return f"""ORIENT phase:
        Query: {query}
        Context: {self._format_context(context)}
        Previous Observations: {self._format_previous_step(previous_steps, "observe")}
        
        How should we interpret this situation?
        Consider:
        1. What are the key patterns or insights?
        2. What are the potential implications?
        3. What assumptions are we making?"""

    def _get_decide_prompt(self, context: Dict[str, Any], query: str, previous_steps: List[Dict[str, Any]]) -> str:
        """Get prompt for decision phase.
        
        Args:
            context: The reasoning context
            query: The user query
            previous_steps: Results from previous steps
            
        Returns:
            str: The formatted prompt for the decide phase
        """
        return f"""DECIDE phase:
        Query: {query}
        Context: {self._format_context(context)}
        Previous Analysis: {self._format_previous_step(previous_steps, "orient")}
        
        What actions should we take?
        Consider:
        1. What are our options?
        2. What are the potential outcomes?
        3. What are the risks and trade-offs?"""

    def _get_act_prompt(self, context: Dict[str, Any], query: str, previous_steps: List[Dict[str, Any]]) -> str:
        """Get prompt for action phase.
        
        Args:
            context: The reasoning context
            query: The user query
            previous_steps: Results from previous steps
            
        Returns:
            str: The formatted prompt for the act phase
        """
        return f"""ACT phase:
        Query: {query}
        Context: {self._format_context(context)}
        Decision: {self._format_previous_step(previous_steps, "decide")}
        
        How should we execute our chosen action?
        Consider:
        1. What specific steps should we take?
        2. How will we measure success?
        3. What adjustments might be needed?"""
  