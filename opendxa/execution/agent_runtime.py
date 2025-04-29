"""Agent runtime for executing plans and managing execution flow."""

from typing import Any, Optional, TYPE_CHECKING
from opendxa.base.execution import RuntimeContext
from opendxa.base.execution.execution_types import ExecutionNode, ExecutionSignal, ExecutionSignalType
from opendxa.execution.planning import Planner
from opendxa.execution.reasoning import Reasoner
from opendxa.common.mixins.loggable import Loggable
from opendxa.base.state import WorldState, ExecutionState

if TYPE_CHECKING:
    from opendxa.agent.agent import Agent
    from opendxa.execution.planning import Plan

class AgentRuntime(Loggable):
    """Runtime for executing agent plans and managing execution flow."""

    def __init__(self, agent: 'Agent'):
        """Initialize agent runtime.
        
        Args:
            agent: The agent instance this runtime belongs to
        """
        super().__init__()
        self._agent = agent
        self._planner = Planner()
        self._reasoner = Reasoner()

    def create_runtime_context(self, plan: 'Plan') -> RuntimeContext:
        """Create a new runtime context for plan execution.
        
        Args:
            plan: The plan to create context for
            
        Returns:
            New runtime context
        """
        agent_state = self._agent.state
        world_state = WorldState()
        execution_state = ExecutionState()

        def handle_plan_get(key: str, default: Any) -> Any:
            return plan.get(key, default) if plan else default

        def handle_plan_set(key: str, value: Any) -> None:
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
            agent_state=agent_state,
            world_state=world_state,
            execution_state=execution_state,
            state_handlers=state_handlers
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
            context = self.create_runtime_context(plan)

        # Execute planning nodes
        for node in plan.planning_nodes:
            result = await self._execute_planning_node(node, context)
            if result.type == ExecutionSignalType.CONTROL_ERROR:
                return result

        # Execute reasoning nodes
        for node in plan.reasoning_nodes:
            result = await self._execute_reasoning_node(node, context)
            if result.type == ExecutionSignalType.CONTROL_ERROR:
                return result

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
        return await self._planner.execute_node(node, context)

    async def _execute_reasoning_node(self, node: ExecutionNode, context: RuntimeContext) -> ExecutionSignal:
        """Execute a reasoning node.
        
        Args:
            node: The node to execute
            context: The runtime context
            
        Returns:
            The result of node execution
        """
        return await self._reasoner.execute_node(node, context)

    async def cleanup(self) -> None:
        """Clean up runtime resources."""
        # Nothing to clean up for now
        pass 