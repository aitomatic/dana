"""
Agent Runtime
"""

from typing import Any, Dict, TYPE_CHECKING, List, Optional
from ..execution.execution_types import ObjectiveStatus, ExecutionSignalType, ExecutionContext
from ..workflow import Workflow
from ..planning import Planner, BasePlan
from ..reasoning import BaseReasoner
from ..resource import BaseResource
from ..state import ExecutionState, WorldState, AgentState
from ..execution.execution_graph import ExecutionNode
from ..execution.execution_types import ExecutionSignal
from ..reasoning.reasoning_factory import ReasoningFactory
from ..planning.planning_factory import PlanningFactory
if TYPE_CHECKING:
    from .agent import Agent


class AgentRuntime:
    """
    Manages agent execution, coordinating between planning and reasoning.
    Handles lifecycle of execution, resource management, and state tracking.
    """
    def __init__(self, agent: "Agent", planning_pattern: str = "sequential", 
                 reasoning_pattern: str = "direct"):
        self.agent = agent
        # Runtime owns and maintains these states
        self._execution_state = ExecutionState()  # Tracks execution progress
        self._world_state = WorldState()         # Tracks discovered knowledge
        self._current_workflow: Optional[Workflow] = None
        
        self.planner = PlanningFactory.create(planning_pattern)
        self.reasoner = ReasoningFactory.create(reasoning_pattern)
        self._workflow_plan_mapping = {}
        self._plan_workflow_mapping = {}

    @property
    def agent_llm(self):
        """Convenient reference to the Agent’s agent_llm"""
        return self.agent.agent_llm
    
    @property
    def planner(self) -> Planner:
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
    
    def get_context(self) -> ExecutionContext:
        """Get execution context with all states."""
        return ExecutionContext(
            agent_state=self.agent.state,
            world_state=self._world_state,
            execution_state=self._execution_state,
            current_workflow=self._current_workflow,
            current_plan=self.agent.state.plan
        )

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
        self._current_workflow = workflow

        # Create plan from workflow pattern
        assert workflow.objective is not None
        plan = await self.planner.create_plan(workflow.objective)
        self._map_workflow_to_plan(workflow, plan)
        self.agent.state.set_plan(plan)  # Agent owns plan

        while not self._is_terminal_state():
            step = self.agent.state.get_current_step()
            if not step:
                break

            # Execute step from plan and collect results
            signals = await self._execute_step(step)
            
            # Process signals and update states
            self._process_signals(signals)

        return self._create_result()

    def _is_terminal_state(self) -> bool:
        """Check if execution should terminate"""
        assert self.agent.state.objective is not None
        return (self.agent.state.objective.status in 
                [ObjectiveStatus.COMPLETED, 
                 ObjectiveStatus.FAILED,
                 ObjectiveStatus.NEEDS_CLARIFICATION])

    def _process_objective_signals(self) -> None:
        """Process any signals that might evolve the objective."""
        for signal in self.agent.state.get_signals():
            if signal.type == ExecutionSignalType.OBJECTIVE_UPDATE:
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

    async def _execute_step(self, step: ExecutionNode) -> List[ExecutionSignal]:
        """Execute a single step from the plan using the reasoner."""
        context = self.get_context()
        signals = await self.reasoner.reason_about(
            step=step,
            context=context,
            agent_llm=self.agent_llm,
            resources=self.resources
        )
        return signals

    def _update_states(self, signals: List[ExecutionSignal]) -> None:
        """Update execution and world states based on signals."""
        for signal in signals:
            # Update world state with discoveries
            if signal.type == ExecutionSignalType.DISCOVERY:
                self._world_state.update(signal.content)
            
            # Update execution state for step completion/failure
            elif signal.type in [ExecutionSignalType.STEP_COMPLETE, ExecutionSignalType.STEP_FAILED]:
                step = self.agent.state.get_current_step()
                if step:
                    self._execution_state.step_results[step.description] = signal.content
                    self.agent.state.advance_step()
            
            # Add signal to agent state for planning
            self.agent.state.add_signal(signal)

    def _process_signals(self, signals: List[ExecutionSignal]) -> None:
        """Process signals at all layers and update states."""
        # Process at each layer
        workflow_signals = self._process_workflow_signals(signals)
        planning_signals = self._process_planning_signals(signals)
        reasoning_signals = self._process_reasoning_signals(signals)
        
        # Update states with all signals
        self._update_states(workflow_signals + planning_signals + reasoning_signals)
        
        # Process objective evolution signals
        self._process_objective_signals()
        
        # Let planner update plan if needed
        if signals and self.agent.state.plan:
            current_index = self.agent.state.current_step_index
            self.planner.update_plan(
                plan=self.agent.state.plan,
                signals=signals,
                from_step_index=current_index
            )

    def _process_workflow_signals(self, signals: List[ExecutionSignal]) -> List[ExecutionSignal]:
        """Process signals at workflow level."""
        workflow_signals = []
        for signal in signals:
            if signal.type == ExecutionSignalType.WORKFLOW_UPDATE:
                workflow = self._get_current_workflow()
                plan = self._workflow_plan_mapping.get(workflow.name)
                if plan:
                    # Update workflow based on signal
                    workflow.update_from_signal(signal)
                    # Generate any new workflow-level signals
                    workflow_signals.extend(workflow.process_signal(signal))
        return workflow_signals

    def _process_planning_signals(self, signals: List[ExecutionSignal]) -> List[ExecutionSignal]:
        """Process signals at planning level."""
        planning_signals = []
        for signal in signals:
            if signal.type in [ExecutionSignalType.DISCOVERY, ExecutionSignalType.STEP_COMPLETE]:
                # Let planner process signal and generate new signals
                new_signals = self.planner.process_signal(signal)
                planning_signals.extend(new_signals)
        return planning_signals

    def _process_reasoning_signals(self, signals: List[ExecutionSignal]) -> List[ExecutionSignal]:
        """Process signals at reasoning level."""
        reasoning_signals = []
        for signal in signals:
            if signal.type == ExecutionSignalType.REASONING_UPDATE:
                # Let reasoner process signal and generate new signals
                new_signals = self.reasoner.process_signal(signal)
                reasoning_signals.extend(new_signals)
        return reasoning_signals

    def _get_current_workflow(self) -> Optional[Workflow]:
        """Get currently executing workflow."""
        return self._current_workflow

    def _map_workflow_to_plan(self, workflow: Workflow, plan: BasePlan) -> None:
        """Map workflow to its execution plan."""
        self._workflow_plan_mapping[workflow.name] = plan
        self._plan_workflow_mapping[plan.id] = workflow

    def _get_workflow_for_plan(self, plan: BasePlan) -> Optional[Workflow]:
        """Get workflow for given plan."""
        return self._plan_workflow_mapping.get(plan.id)