"""
Agent Runtime
"""

from typing import Any, Dict, TYPE_CHECKING, List
from ..types import ObjectiveStatus, SignalType
from ..workflow import Workflow
from ..planning import BasePlanner, PlanNode
from ..reasoning import BaseReasoner
from ..resource import BaseResource
from ..state import ExecutionState, WorldState
from ..types import Signal
if TYPE_CHECKING:
    from .agent import Agent


class AgentRuntime:
    """
    Manages agent execution, coordinating between planning and reasoning.
    Handles lifecycle of execution, resource management, and state tracking.
    """
    def __init__(self, agent: "Agent"):
        self.agent = agent
        # Runtime owns and maintains these states
        self._execution_state = ExecutionState()  # Tracks execution progress
        self._world_state = WorldState()         # Tracks discovered knowledge
        
        # Context provides read access to all states
        self._context = {
            "agent_state": self.agent.state,     # Owned by Agent
            "execution": self._execution_state,   # Owned by Runtime
            "world": self._world_state,          # Owned by Runtime
        }

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
    def resources(self) -> Dict[str, BaseResource]:
        """Convenient reference to the Agent’s resources"""
        return self.agent.resources
    
    @property
    def execution_state(self) -> ExecutionState:
        """Get execution state."""
        return self._execution_state
    
    @property
    def world_state(self) -> WorldState:
        """Get world state."""
        return self._world_state
    
    def get_context(self) -> Dict[str, Any]:
        """Get read-only context with all states."""
        return self._context.copy()

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

    async def execute(self, workflow: Workflow) -> Any:
        """Execute using workflow as reference pattern."""
        # Initialize execution state
        self._execution_state.reset()
        self._world_state.reset()

        # Create plan from workflow pattern
        plan = await self.planner.create_plan(workflow.objective)
        self.agent.state.set_plan(plan)  # Agent owns plan

        while not self._is_terminal_state():
            step = self.agent.state.get_current_step()
            if not step:
                break

            # Execute step from plan (not workflow) and collect results
            signals = await self._execute_step(step)
            
            # Update states based on results
            self._update_states(signals)
            
            # Let planner process signals and potentially update plan
            self._process_planning_results(signals)

        return self._create_result()

    def _is_terminal_state(self) -> bool:
        """Check if execution should terminate"""
        return (self.agent.state.objective.status in 
                [ObjectiveStatus.COMPLETED, 
                 ObjectiveStatus.FAILED,
                 ObjectiveStatus.NEEDS_CLARIFICATION])

    def _process_objective_signals(self) -> None:
        """Process any signals that might evolve the objective."""
        for signal in self.agent.state.get_signals():
            if signal.type == SignalType.OBJECTIVE_UPDATE:
                new_objective = signal.content.get("new_objective")
                reason = signal.content.get("reason")
                if new_objective:
                    self.agent.state.objective.evolve(new_objective, reason)

    def _create_result(self) -> Any:
        """Create final result from state"""
        # Could be customized based on objective type
        return {
            "status": self.agent.state.objective.status,
            "result": self.agent.state.plan.steps[-1].result if self.agent.state.plan.steps else None,
            "objective": {
                "original": self.agent.state.objective.original,
                "final": self.agent.state.objective.current
            }
        }

    async def _execute_step(self, step: PlanNode) -> List[Signal]:
        """Execute a single step from the plan using the reasoner."""
        context = self.get_context()
        signals = await self.reasoner.reason_about(
            step=step,
            context=context,
            agent_llm=self.agent_llm,
            resources=self.resources
        )
        return signals

    def _update_states(self, signals: List[Signal]) -> None:
        """Update execution and world states based on signals."""
        for signal in signals:
            # Update world state with discoveries
            if signal.type == SignalType.DISCOVERY:
                self._world_state.update(signal.content)
            
            # Update execution state for step completion/failure
            elif signal.type in [SignalType.STEP_COMPLETE, SignalType.STEP_FAILED]:
                step = self.agent.state.get_current_step()
                if step:
                    self._execution_state.step_results[step.description] = signal.content
                    self.agent.state.advance_step()
            
            # Add signal to agent state for planning
            self.agent.state.add_signal(signal)

    def _process_planning_results(self, signals: List[Signal]) -> None:
        """Process signals that may affect planning."""
        # Process objective evolution signals
        self._process_objective_signals()
        
        # Let planner update plan if needed based on signals
        if signals and self.agent.state.plan:
            current_index = self.agent.state.current_step_index
            self.planner.update_plan(
                plan=self.agent.state.plan,
                signals=signals,
                from_step_index=current_index
            )