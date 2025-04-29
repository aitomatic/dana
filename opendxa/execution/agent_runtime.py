"""Agent runtime for executing plans and managing execution flow."""

from typing import Any, Optional, TYPE_CHECKING
from opendxa.base.execution import RuntimeContext
from opendxa.base.execution.execution_types import ExecutionNode, ExecutionSignal, ExecutionSignalType
from opendxa.common.mixins.loggable import Loggable
from opendxa.base.state import WorldState, ExecutionState
from opendxa.execution.planning import Plan
from opendxa.execution.planning import Planner
if TYPE_CHECKING:
    from opendxa.agent.agent import Agent

class AgentRuntime(Loggable):
    """Runtime for executing agent plans and managing execution flow."""

    def __init__(self, agent: 'Agent'):
        """Initialize agent runtime.
        
        Args:
            agent: The agent instance this runtime belongs to
        """
        super().__init__()
        self._agent = agent

    @property
    def _planner(self) -> Planner:
        """Convenience property for accessing the planner."""
        return self._agent.planner
    
    @property
    def _current_plan(self) -> Plan:
        """Convenience property for accessing the current plan."""
        return self._agent.planner.get_current_plan()

    def create_runtime_context(self) -> RuntimeContext:
        """Create a new runtime context for plan execution.
        
        Returns:
            New runtime context
        """
        agent_state = self._agent.state
        world_state = WorldState()
        execution_state = ExecutionState()

        def handle_plan_get(key: str, default: Any) -> Any:
            plan = self._current_plan
            return plan.get(key, default) if plan else default

        def handle_plan_set(key: str, value: Any) -> None:
            plan = self._current_plan
            if plan:
                plan.set(key, value)
            else:
                raise ReferenceError("Cannot set plan state: no plan provided")

        state_handlers = {
            'plan': {
                'get': handle_plan_get,
                'set': handle_plan_set
            }
        }

        return RuntimeContext(
            agent=self._agent,
            agent_state=agent_state,
            world_state=world_state,
            execution_state=execution_state,
            state_handlers=state_handlers,
        )

    async def execute(self, plan: 'Plan', context: Optional[RuntimeContext] = None) -> Any:
        """Execute a plan.
        
        Args:
            plan: The plan to execute
            context: Optional runtime context. If None, a new one will be created.
            
        Returns:
            The result of plan execution
        """
        if context is None:
            context = self.create_runtime_context()

        self._planner.execute(plan, context)

        return ExecutionSignal(
            type=ExecutionSignalType.CONTROL_COMPLETE,
            content={"success": True}
        )

    async def _execute_planning_node(self, node: ExecutionNode, context: RuntimeContext) -> ExecutionSignal:
        """Execute a planning node.
        
        Args:
            node: The node to execute
            context: The runtime context
            
        Returns:
            The result of node execution
        """
        return await self._planner.execute(node, context)

    async def cleanup(self) -> None:
        """Clean up runtime resources."""
        # Nothing to clean up for now
        pass 