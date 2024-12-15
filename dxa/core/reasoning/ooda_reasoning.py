"""OODA (Observe-Orient-Decide-Act) Reasoning Pattern.

A cyclical reasoning pattern for dynamic situations:

Key Features:
- Continuous adaptation through OODA loop
- Real-time situation assessment
- Dynamic decision making
- Feedback-driven improvements

Best For:
- Dynamic environments
- Strategic planning
- Competitive situations
- When conditions change frequently

Example:
    ```python
    reasoning = OODAReasoning()
    result = await reasoning.execute(
        task={"objective": "Navigate changing market conditions"},
        context=context
    )
    ```

Cycle:
1. Observe: Gather current situation data
2. Orient: Analyze and understand context
3. Decide: Choose best action
4. Act: Execute and gather feedback
"""

from typing import Dict, Any, List, Optional
from dxa.core.reasoning.base_reasoning import (
    BaseReasoning, 
    ReasoningResult, 
    ReasoningContext,
    StepResult,
    ReasoningStatus
)

class OODAReasoning(BaseReasoning):
    """OODA loop implementation with continuous adaptation."""
    
    @property
    def steps(self) -> List[str]:
        return ["observe", "orient", "decide", "act"]
    
    def get_initial_step(self) -> str:
        # If we have prior observations in context, we might start at 'orient'
        if self.previous_steps and self.previous_steps[-1]["step"] == "act":
            return "orient"  # Skip observe if we just acted
        return "observe"  # Otherwise start with observation

    async def _core_execute(self, 
                          task: Dict[str, Any],
                          context: ReasoningContext) -> ReasoningResult:
        await self._init_objective(context)
        cycles = 0
        max_cycles = 5  # Prevent infinite loops
        
        while cycles < max_cycles:
            cycles += 1
            
            # OBSERVE: Gather current situation data
            observation = await self._observe(task, context)
            if observation.status != ReasoningStatus.COMPLETE:
                return self._create_error_result("Failed observation", observation)
                
            # ORIENT: Analyze and understand current situation
            orientation = await self._orient(observation, context)
            if orientation.status != ReasoningStatus.COMPLETE:
                return self._create_error_result("Failed orientation", orientation)
                
            # DECIDE: Choose next action
            decision = await self._decide(orientation, context)
            if decision.status != ReasoningStatus.COMPLETE:
                return self._create_error_result("Failed decision", decision)
                
            # ACT: Execute decided action
            action = await self._act(decision, context)
            if action.status != ReasoningStatus.COMPLETE:
                return self._create_error_result("Failed action", action)
                
            # Check if objective is met
            if await self._is_objective_met(action, context):
                return ReasoningResult(
                    success=True,
                    output=action.content,
                    insights={
                        "cycles": cycles,
                        "objective_evolution": self.objective_state.refinements,
                        "final_objective": self.objective_state.current
                    },
                    confidence=0.8,  # OODA acknowledges uncertainty
                    reasoning_path=self._get_cycle_path(cycles)
                )
                
            # Update context for next cycle
            context.workspace.update({
                "last_observation": observation.content,
                "last_orientation": orientation.content,
                "last_action": action.content,
                "cycle": cycles
            })
            
        # If we reach here, we hit max cycles
        return ReasoningResult(
            success=False,
            output="Max cycles reached without meeting objective",
            insights={
                "cycles": cycles,
                "objective_evolution": self.objective_state.refinements
            },
            confidence=0.0,
            reasoning_path=self._get_cycle_path(cycles)
        )

    async def _observe(self, task: Dict[str, Any], context: ReasoningContext) -> StepResult:
        """Gather and analyze current situation."""
        prompt = f"""
        OBSERVE phase:
        Current Objective: {context.objective}
        Task: {task.get('command')}
        Previous Actions: {context.workspace.get('last_action', 'None')}
        
        Observe the current situation:
        1. What information do we have?
        2. What has changed since last action?
        3. What patterns or anomalies do we notice?
        4. What additional information might we need?
        """
        
        response = await self._query_agent_llm({
            "prompt": prompt,
            "system_prompt": "You are in the OBSERVE phase of OODA."
        })
        
        return StepResult(
            status=ReasoningStatus.COMPLETE,
            content=response["response"]
        )

    async def _orient(self, observation: StepResult, context: ReasoningContext) -> StepResult:
        """Analyze and understand the situation."""
        prompt = f"""
        ORIENT phase:
        Current Objective: {context.objective}
        Observations: {observation.content}
        
        Orient to the situation:
        1. What does this mean for our objective?
        2. What are the key factors affecting our situation?
        3. What options are available to us?
        4. What constraints do we face?
        """
        
        response = await self._query_agent_llm({
            "prompt": prompt,
            "system_prompt": "You are in the ORIENT phase of OODA."
        })
        
        return StepResult(
            status=ReasoningStatus.COMPLETE,
            content=response["response"]
        )

    async def _decide(self, orientation: StepResult, context: ReasoningContext) -> StepResult:
        """Choose next action based on orientation."""
        prompt = f"""
        DECIDE phase:
        Current Objective: {context.objective}
        Orientation: {orientation.content}
        
        Decide on next action:
        1. What are our options?
        2. What are the potential outcomes?
        3. What are the risks?
        4. What is our best course of action?
        """
        
        response = await self._query_agent_llm({
            "prompt": prompt,
            "system_prompt": "You are in the DECIDE phase of OODA."
        })
        
        return StepResult(
            status=ReasoningStatus.COMPLETE,
            content=response["response"]
        )

    async def _act(self, decision: StepResult, context: ReasoningContext) -> StepResult:
        """Execute the decided action."""
        prompt = f"""
        ACT phase:
        Current Objective: {context.objective}
        Decision: {decision.content}
        
        Execute the action:
        1. What specific steps should we take?
        2. How will we measure success?
        3. What feedback should we look for?
        4. What adjustments might be needed?
        """
        
        response = await self._query_agent_llm({
            "prompt": prompt,
            "system_prompt": "You are in the ACT phase of OODA."
        })
        
        return StepResult(
            status=ReasoningStatus.COMPLETE,
            content=response["response"]
        )

    async def _is_objective_met(self, action: StepResult, context: ReasoningContext) -> bool:
        """Check if current action meets objective."""
        prompt = f"""
        Evaluate objective completion:
        Original Objective: {self.objective_state.original}
        Current Objective: {self.objective_state.current}
        Latest Action Result: {action.content}
        
        Has the objective been met? Answer Yes or No and explain why.
        """
        
        response = await self._query_agent_llm({
            "prompt": prompt,
            "system_prompt": "You are evaluating objective completion."
        })
        
        return "yes" in response["response"].lower()

    def _create_error_result(self, message: str, step_result: StepResult) -> ReasoningResult:
        """Create error result from failed step."""
        return ReasoningResult(
            success=False,
            output=step_result.content,
            insights={
                "error": message,
                "objective_evolution": self.objective_state.refinements
            },
            confidence=0.0,
            reasoning_path=self._get_cycle_path()
        )

    def _get_cycle_path(self, cycles: int = 0) -> List[str]:
        """Get the OODA cycles executed."""
        path = []
        for i in range(cycles):
            path.extend([f"cycle{i+1}_" + step for step in self.steps])
        return path
  