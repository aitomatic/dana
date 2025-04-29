"""Manages the runtime context for OpenDXA components.

This module provides the core RuntimeContext class that manages the state and
configuration for OpenDXA components. It supports two types of state access:

1. Direct state container access using dot notation
2. Custom state handlers for special processing

The runtime context provides a unified interface for accessing and modifying
state across different containers and handlers.
"""

from typing import Optional, Dict, Any, List, Callable, TYPE_CHECKING
from opendxa.base.state.agent_state import AgentState
from opendxa.base.state.world_state import WorldState
from opendxa.base.state.execution_state import ExecutionState, ExecutionStatus
from opendxa.base.state.state_manager import StateManager
from opendxa.common.mixins.loggable import Loggable

if TYPE_CHECKING:
    from opendxa.agent.agent import Agent

class RuntimeContext(Loggable):
    """Interface for runtime operations and coordination.
    
    This class provides the interface for executing plans and nodes,
    coordinating between plan and reasoning layers, and managing the
    runtime flow. It does not maintain state directly, but instead
    works with an ExecutionState instance to track execution progress.
    
    The context is responsible for:
    - Executing plans from start to finish
    - Executing individual nodes
    - Coordinating between plan and reasoning layers
    - Managing runtime flow and transitions
    - Processing execution signals and events
    
    It should be used as the primary interface for all runtime operations,
    while the ExecutionState handles state management. The context ensures
    that state changes are properly coordinated and validated through the
    ExecutionState instance.
    
    Example:
        ```python
        # Create state and context
        state = ExecutionState()
        context = RuntimeContext(state)
        
        # Execute a plan
        plan = Plan(...)
        await context.execute_plan(plan)
        ```
    
    Attributes:
        _state: The ExecutionState instance managing execution state
    """

    def __init__(self,
                 agent: 'Agent',
                 agent_state: AgentState,
                 world_state: WorldState,
                 execution_state: ExecutionState,
                 state_handlers: Optional[Dict[str, Dict[str, Callable]]] = None):
        """Initializes the execution context with state containers and handlers.
        
        The initialization process:
        1. Creates state containers for agent, world, and execution state
        2. Initializes StateManager with state containers and handlers
        
        Args:
            agent_state: The agent state container
            world_state: The world state container
            execution_state: The execution state container
            state_handlers: Optional dictionary mapping prefixes to handler functions.
                           Each prefix should map to a dictionary with 'get' and/or 'set'
                           keys mapping to handler functions.
                           These will be called when accessing state with their prefix.
        """
        super().__init__()
        self._state = execution_state

        # Initialize StateManager with state containers and handlers
        self._state_manager = StateManager(
            state_containers={
                'agent': agent_state,
                'world': world_state,
                'execution': execution_state
            },
            state_handlers=state_handlers
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value using a unified key string.
        
        Args:
            key: The unified key string (e.g., 'plan.id', 'agent.user.name')
            default: The value to return if the key is not found

        Returns:
            The retrieved value, or the default value if not found
        """
        return self._state_manager.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value using a unified key string.
        
        Args:
            key: The unified key string (e.g., 'plan.objective', 'agent.user.name')
            value: The value to set
        
        Raises:
            ValueError: If the key format is invalid or attempts to set read-only key
            KeyError: If the prefix is unknown
        """
        self._state_manager.set(key, value)

    def _initialize_execution_state(self) -> None:
        """Initialize execution state tracking."""
        self._state_manager.set('execution.status', ExecutionStatus.IDLE)
        self._state_manager.set('execution.current_node_id', None)
        self._state_manager.set('execution.step_results', {})
        self._state_manager.set('execution.visited_nodes', [])
        self._state_manager.set('execution.node_results', {})
        self._state_manager.set('execution.execution_path', [])

    def reset_execution_state(self) -> None:
        """Reset execution state to initial values."""
        self._initialize_execution_state()

    def update_execution_node(self, node_id: str, result: Optional[Any] = None) -> None:
        """Update current node and record result.
        
        Args:
            node_id: ID of the node to update to
            result: Optional result from the node execution
        """
        # Update context manager state
        current_node_id = self._state_manager.get('execution.current_node_id')
        if current_node_id:
            path = self._state_manager.get('execution.execution_path', [])
            path.append((current_node_id, node_id))
            self._state_manager.set('execution.execution_path', path)
            
        self._state_manager.set('execution.current_node_id', node_id)
        
        visited_nodes = self._state_manager.get('execution.visited_nodes', [])
        visited_nodes.append(node_id)
        self._state_manager.set('execution.visited_nodes', visited_nodes)
        
        if result is not None:
            node_results = self._state_manager.get('execution.node_results', {})
            node_results[node_id] = result
            self._state_manager.set('execution.node_results', node_results)

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution history with results.
        
        Returns:
            List of dictionaries containing node IDs and their results
        """
        visited_nodes = self._state_manager.get('execution.visited_nodes', [])
        node_results = self._state_manager.get('execution.node_results', {})
        
        return [
            {
                "node_id": node_id,
                "result": node_results.get(node_id)
            }
            for node_id in visited_nodes
        ]

    def build_llm_context(self) -> Dict[str, Any]:
        """Build context potentially useful for LLM calls.

        Note: The exact context needed varies greatly. This provides a basic structure.
        It retrieves plan/reasoning results assuming they are stored in the 
        transient state via store_node_output under standard keys.
        
        Returns:
            Dictionary containing potentially relevant context.
        """
        current_node_id = self._state_manager.get('execution.current_node_id')
        
        # Retrieve relevant state using the state manager
        current_objective = self._state_manager.get("temp.objective")
        plan_result = self._state_manager.get(f"temp.plan_results.{current_node_id}")
        reasoning_results = self._state_manager.get(f"temp.reasoning_results.{current_node_id}", default={})

        llm_context = {
            "current_objective": current_objective,
            "step_results": {
                "plan": plan_result,
                "reasoning": reasoning_results
            }
        }
        return llm_context

    def store_node_output(self, node_id: str, result: Any) -> None:
        """Process the output mappings defined in the plan for a given node.
        
        Uses the state manager to store the results.
        
        Args:
            node_id: The ID of the node whose result is being stored.
            result: The structured result dictionary from the node execution.
        """
        if not isinstance(result, dict):
            self.warning(f"Cannot process output mappings for node '{node_id}' because result is not a dictionary.")
            return

        for result_field, destination_string in result.items():
            if not isinstance(destination_string, str):
                self.warning(f"Invalid destination '{destination_string}' for field '{result_field}' in node '{node_id}'. Skipping.")
                continue
                 
            value_to_store = result.get(result_field)
            if value_to_store is None:
                if result_field not in result:
                    self.warning(f"Field '{result_field}' not in result for node '{node_id}'. Skipping {destination_string}.")
                    continue
            
            try:
                self._state_manager.set(destination_string, value_to_store)
            except Exception as e:
                self.error(f"Failed to store field '{result_field}' to '{destination_string}' for node '{node_id}': {e}")
                continue
