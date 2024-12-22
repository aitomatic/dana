"""
Agent Runtime
"""

from typing import Any, TYPE_CHECKING, List
from ..types import Objective, Signal, ObjectiveStatus, SignalType
from ..planning.base_planner import BasePlanner
from ..reasoning.base_reasoner import BaseReasoner
from ..resource.base_resource import BaseResource
from .agent_state import AgentState
if TYPE_CHECKING:
    from .agent import Agent


class AgentRuntime:
    """
    Manages agent execution, coordinating between planning and reasoning.
    Handles lifecycle of execution, resource management, and state tracking.
    """
    def __init__(self, agent: "Agent"):
        self.agent = agent
    
    @property
    def agent_llm(self):
        """Convenient reference to the Agent’s agent_llm"""
        return self.agent.agent_llm
    
    @property
    def planner(self) -> BasePlanner:
        """Convenient reference to the Agent’s planner"""
        return self.agent.planner

    @property
    def reasoner(self) -> BaseReasoner:
        """Convenient reference to the Agent’s reasoner"""
        return self.agent.reasoner

    @property
    def resources(self) -> List[BaseResource]:
        """Convenient reference to the Agent’s resources"""
        return self.agent.resources
    
    @property
    def agent_state(self) -> AgentState:
        """Convenient reference to the Agent’s state"""
        return self.agent.state

    async def initialize(self) -> None:
        """Initialize runtime and resources"""
        await self.agent_llm.initialize()
        for resource in self.resources.values():
            if hasattr(resource, 'initialize'):
                await resource.initialize()

    async def cleanup(self) -> None:
        """Cleanup runtime and resources"""
        await self.agent_llm.cleanup()
        for resource in self.resources.values():
            if hasattr(resource, 'cleanup'):
                await resource.cleanup()

    async def execute(self, objective: str, **kwargs) -> Any:
        """Execute an objective using planning and reasoning."""
        # Initialize state if not already done
        if not self.agent_state:
            self.agent_state = AgentState()
        
        # Create objective from string
        objective = Objective(
            original=objective,
            current=objective,
            status=ObjectiveStatus.INITIAL
        )
        
        # Update state
        self.agent_state.set_objective(objective)  # Use set_objective method
        
        # Create and execute plan
        plan = await self.planner.create_plan(objective)
        self.agent_state.set_plan(plan)

        # Execute until complete or clarification needed
        while not self._is_terminal_state():
            # Get current step
            step = self.agent_state.get_current_step()
            if not step:
                break

            try:
                import pytest ; pytest.set_trace()

                # Execute step with reasoning
                reasoning_signals = await self.reasoner.reason_about(
                    step=step,
                    context=self.agent_state.get_context(),
                    agent_llm=self.agent_llm,
                    resources=self.resources
                )
                
                # Process through planning
                new_plan, planning_signals = self.planner.process_signals(
                    self.agent_state.plan,
                    reasoning_signals  # Pass reasoning signals directly
                )

                # Update state with new plan and signals
                if new_plan:
                    self.agent_state.set_plan(new_plan)

                self.agent_state.clear_signals()  # Clear before adding new ones
                for signal in planning_signals:  # Add only planning signals
                    self.agent_state.add_signal(signal)

                # Process any objective evolution signals
                self._process_objective_signals()

                # Advance to next step
                self.agent_state.advance_step()

            # pylint: disable=broad-exception-caught
            except Exception as e:
                # Handle errors by converting to signals
                self.agent_state.add_signal(Signal(
                    type=SignalType.STEP_FAILED,
                    content={"error": str(e)}
                ))

        return self._create_result()

    def _is_terminal_state(self) -> bool:
        """Check if execution should terminate"""
        return (self.agent_state.objective.status in 
                [ObjectiveStatus.COMPLETED, 
                 ObjectiveStatus.FAILED,
                 ObjectiveStatus.NEEDS_CLARIFICATION])

    def _process_objective_signals(self) -> None:
        """Process any signals that might evolve the objective."""
        for signal in self.agent_state.get_signals():
            if signal.type == SignalType.OBJECTIVE_UPDATE:
                new_objective = signal.content.get("new_objective")
                reason = signal.content.get("reason")
                if new_objective:
                    self.agent_state.objective.evolve(new_objective, reason)

    def _create_result(self) -> Any:
        """Create final result from state"""
        # Could be customized based on objective type
        return {
            "status": self.agent_state.objective.status,
            "result": self.agent_state.plan.steps[-1].result if self.agent_state.plan.steps else None,
            "objective": {
                "original": self.agent_state.objective.original,
                "final": self.agent_state.objective.current
            }
        }