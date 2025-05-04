"""Manages the runtime context for OpenDXA components.

This module provides the core RuntimeContext class that manages the state and
configuration for OpenDXA components. It supports two types of state access:

1. Direct state container access using dot notation
2. Custom state handlers for special processing

The runtime context provides a unified interface for accessing and modifying
state across different containers and handlers.
"""

from typing import Optional, Dict, Any, List, Callable
from pydantic import BaseModel, Field
from opendxa.base.state.agent_state import AgentState
from opendxa.base.state.world_state import WorldState
from opendxa.base.state.execution_state import ExecutionState, ExecutionStatus
from opendxa.base.state.state_manager import StateManager

class RuntimeContext(BaseModel):
    """Holds the runtime context for execution, delegating state to StateManager."""
    
    # State Manager handles access to various state components
    _state_manager: StateManager = Field(exclude=True)  # Exclude from Pydantic model fields

    # Removed: Core execution state current_node_id 
    # Removed: Flexible data storage _data
    
    def __init__(self,
                 agent_state: AgentState,
                 world_state: WorldState,
                 execution_state: ExecutionState,
                 state_handlers: Optional[Dict[str, Dict[str, Callable]]] = None,
                 **data: Any  # Allow passing other Pydantic fields if needed
                 ):
        """Initializes the execution context with state containers and handlers."""
        # Initialize Pydantic fields first if any were passed via data
        super().__init__(**data)
        
        # Initialize StateManager with state containers and handlers
        self._state_manager = StateManager(
            state_containers={
                'agent': agent_state,
                'world': world_state,
                'execution': execution_state
            },
            state_handlers=state_handlers
        )
        # NOTE: Removed self._state = execution_state as StateManager now holds it under 'execution'

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """Get a value from the context via the StateManager."""
        # Delegate to StateManager
        return self._state_manager.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context via the StateManager."""
        # Delegate to StateManager
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

    def clone(self) -> 'RuntimeContext':
        """Create a copy of the context.
        WARNING: This performs a shallow copy of the state manager and underlying 
        state containers by default with Pydantic copy. Deep state isolation 
        might require custom cloning logic if needed.
        """
        new_context = self.model_copy(deep=False)  # Use shallow copy primarily
        return new_context

    # Allow arbitrary types for flexibility in underlying state containers if needed by StateManager
    model_config = {"arbitrary_types_allowed": True}
