from typing import Dict, Any, Optional

from dxa.core.planning.base_planning import BasePlanning
from dxa.core.reasoning.base_reasoning import BaseReasoning
from dxa.agent.agent_state import AgentState
from dxa.core.types import Objective, Signal, ObjectiveStatus, SignalType

class AgentRuntime:
    """
    Manages agent execution, coordinating between planning and reasoning.
    Handles lifecycle of execution, resource management, and state tracking.
    """
    def __init__(self,
                 planning: BasePlanning,
                 reasoning: BaseReasoning,
                 resources: Dict[str, Any]):
        self.planning = planning
        self.reasoning = reasoning
        self.resources = resources
        self.state: Optional[AgentState] = None

    async def initialize(self) -> None:
        """Initialize runtime and resources"""
        # Initialize resources
        for resource in self.resources.values():
            if hasattr(resource, 'initialize'):
                await resource.initialize()

    async def cleanup(self) -> None:
        """Cleanup runtime and resources"""
        # Cleanup resources
        for resource in self.resources.values():
            if hasattr(resource, 'cleanup'):
                await resource.cleanup()

    async def execute(self, objective: str) -> Any:
        """
        Execute an objective:
        1. Create initial state with objective
        2. Get plan from planning
        3. Execute steps via reasoning
        4. Process signals and update state
        5. Continue until completion/clarification needed
        """
        # Initialize state
        self.state = AgentState(
            objective=Objective(original=objective, current=objective)
        )
        self.state.objective.status = ObjectiveStatus.IN_PROGRESS

        # Get initial plan
        plan = await self.planning.create_plan(self.state.objective)
        self.state.set_plan(plan)

        # Execute until complete or clarification needed
        while not self._is_terminal_state():
            # Get current step
            step = self.state.get_current_step()
            if not step:
                break

            try:
                # Execute step with reasoning
                signals = await self.reasoning.reason_about(
                    step=step,
                    context=self.state.get_context(),
                    resources=self.resources
                )
                
                # Add signals to state
                for signal in signals:
                    self.state.add_signal(signal)

                # Process signals through planning
                new_plan, new_signals = await self.planning.process_signals(
                    self.state.plan,
                    self.state.get_signals()
                )

                # Update state based on planning results
                if new_plan:
                    self.state.set_plan(new_plan)
                for signal in new_signals:
                    self.state.add_signal(signal)

                # Process any objective evolution signals
                await self._process_objective_signals()

                # Clear processed signals
                self.state.clear_signals()

            # pylint: disable=broad-exception-caught
            except Exception as e:
                # Handle errors by converting to signals
                self.state.add_signal(Signal(
                    type=SignalType.STEP_FAILED,
                    content={"error": str(e)}
                ))

        return self._create_result()

    def _is_terminal_state(self) -> bool:
        """Check if execution should terminate"""
        return (self.state.objective.status in 
                [ObjectiveStatus.COMPLETED, 
                 ObjectiveStatus.FAILED,
                 ObjectiveStatus.NEEDS_CLARIFICATION])

    async def _process_objective_signals(self) -> None:
        """Process any signals that might evolve the objective"""
        for signal in self.state.get_signals():
            if signal.type == SignalType.OBJECTIVE_UPDATE:
                new_objective = signal.content.get("new_objective")
                reason = signal.content.get("reason")
                if new_objective:
                    self.state.objective.evolve(new_objective, reason)

    def _create_result(self) -> Any:
        """Create final result from state"""
        # Could be customized based on objective type
        return {
            "status": self.state.objective.status,
            "result": self.state.plan.steps[-1].result if self.state.plan.steps else None,
            "objective": {
                "original": self.state.objective.original,
                "final": self.state.objective.current
            }
        }