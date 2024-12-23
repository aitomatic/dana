"""
Agent Runtime
"""

from typing import Any, Dict, List, TYPE_CHECKING
from ..types import ObjectiveStatus, SignalType
from ..workflow import BaseFlow
from ..planning.base_planner import BasePlanner
from ..reasoning.base_reasoner import BaseReasoner
from ..resource.base_resource import BaseResource
from ..state import ExecutionState, WorldState, FlowState
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
        self._flow_state = FlowState()          # Tracks flow progress
        
        # Context provides read access to all states
        self._context = {
            "agent_state": self.agent.state,     # Owned by Agent
            "execution": self._execution_state,   # Owned by Runtime
            "world": self._world_state,          # Owned by Runtime
            "flow": self._flow_state             # Owned by Runtime
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
    def resources(self) -> List[BaseResource]:
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
    
    @property
    def flow_state(self) -> FlowState:
        """Get flow state."""
        return self._flow_state

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

    async def execute(self, flow: BaseFlow) -> Any:
        """Execute using flow as reference pattern."""
        # Initialize execution state
        self._execution_state.reset()
        self._world_state.reset()
        self._flow_state.set_flow(flow)

        # Create and execute plan
        plan = await self.planner.create_plan(flow.objective)
        self.agent.state.set_plan(plan)  # Agent owns plan

        while not self._is_terminal_state():
            step = self.agent.state.get_current_step()
            if not step:
                break

            # Execute step and collect results
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