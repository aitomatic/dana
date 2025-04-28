"""Manages the execution context for OpenDXA components.

This module provides the core ExecutionContext class that manages the state and
configuration for OpenDXA components. It supports two types of state access:

1. Direct state container access using dot notation
2. Custom state handlers for special processing

The execution context provides a unified interface for accessing and modifying
state across different containers and handlers.
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from opendxa.base.state.agent_state import AgentState
from opendxa.base.state.world_state import WorldState
from opendxa.base.state.execution_state import ExecutionState, ExecutionStatus
from opendxa.base.execution.execution_context_helper import ExecutionContextHelper
from opendxa.base.execution.execution_types import ExecutionNode
from opendxa.common.mixins.loggable import Loggable

log = logging.getLogger(__name__)

class ExecutionContext(Loggable):
    """Manages the execution context for OpenDXA components.

    This class provides a unified interface for managing state and configuration
    across different OpenDXA components. It supports two types of state access:

    1. Standard State Containers:
       - Direct access to state containers using dot notation
       - Managed by StateManager through ExecutionContextHelper
       - Example: 'agent.user.name', 'world.environment.temperature'

    2. Custom State Handlers:
       - Special processing for certain state types
       - Handled by registered state handlers
       - Example: 'plan.objective', 'plan.id'

    The execution context follows a consistent state access pattern:
    1. Parse key into prefix and subkey
    2. Check for state handler first
    3. Fall back to standard state access

    Usage:
        # Create state containers
        agent_state = AgentState()
        world_state = WorldState()
        execution_state = ExecutionState()

        # Define state handlers for custom prefixes
        def handle_plan_get(key: str, default: Any) -> Any:
            return context.get_plan_state(key, default)
            
        def handle_plan_set(key: str, value: Any) -> None:
            context.set_plan_state(key, value)

        # Create execution context
        context = ExecutionContext(
            agent_state=agent_state,
            world_state=world_state,
            execution_state=execution_state,
            state_handlers={
                'plan': {
                    'get': handle_plan_get,
                    'set': handle_plan_set
                }
            }
        )

        # Use the context
        value = context.get('plan.objective')
        context.set('plan.objective', 'new objective')
    """

    def __init__(self,
                 agent_state: AgentState,
                 world_state: WorldState,
                 execution_state: ExecutionState,
                 state_handlers: Optional[Dict[str, Dict[str, Callable]]] = None):
        """Initializes the execution context with state containers and handlers.
        
        The initialization process:
        1. Creates state containers for agent, world, and execution state
        2. Initializes ExecutionContextHelper with state containers and handlers
        3. Sets up plan state management
        
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
        self._agent_state = agent_state
        self._world_state = world_state
        self._execution_state = execution_state
        self._current_plan = None

        # Initialize ExecutionContextHelper with state containers and handlers
        # This will manage both standard state access and custom state handlers
        self._helper = ExecutionContextHelper(
            context=self,
            state_containers={
                'agent': self._agent_state,
                'world': self._world_state,
                'execution': self._execution_state
            },
            state_handlers=state_handlers
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value using a unified key string.
        
        The get operation follows this flow:
        1. Parse the key into prefix and subkey
        2. If prefix has a state handler, use it
        3. Otherwise, delegate to ExecutionContextHelper
        
        Args:
            key: The unified key string (e.g., 'plan.id', 'agent.user.name')
            default: The value to return if the key is not found

        Returns:
            The retrieved value, or the default value if not found
        """
        return self._helper.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value using a unified key string.
        
        The set operation follows this flow:
        1. Parse the key into prefix and subkey
        2. If prefix has a state handler, use it
        3. Otherwise, delegate to ExecutionContextHelper
        
        Args:
            key: The unified key string (e.g., 'plan.objective', 'agent.user.name')
            value: The value to set
        
        Raises:
            ValueError: If the key format is invalid or attempts to set read-only key
            KeyError: If the prefix is unknown
            ReferenceError: If trying to set 'plan.objective' but current_plan is None
        """
        self._helper.set(key, value)

    def get_plan_state(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the current plan's state.
        
        This method provides direct access to plan state values.
        It is used by the plan state handler in ExecutionContextHelper.
        
        Args:
            key: The key to retrieve from the plan state
            default: The value to return if the key is not found

        Returns:
            The retrieved value, or the default value if not found
        """
        if self._current_plan is None:
            return default
        return self._current_plan.get(key, default)

    def set_plan_state(self, key: str, value: Any) -> None:
        """Set a value in the current plan's state.
        
        This method provides direct access to plan state values.
        It is used by the plan state handler in ExecutionContextHelper.
        
        Args:
            key: The key to set in the plan state
            value: The value to set
        
        Raises:
            ReferenceError: If current_plan is None
        """
        if self._current_plan is None:
            raise ReferenceError("Cannot set plan state: no current plan")
        self._current_plan.set(key, value)

    def _initialize_execution_state(self) -> None:
        """Initialize execution state tracking."""
        self._execution_state.reset()
        self._helper.set('execution.status', ExecutionStatus.IDLE)
        self._helper.set('execution.current_node_id', None)
        self._helper.set('execution.step_results', {})
        self._helper.set('execution.visited_nodes', [])
        self._helper.set('execution.node_results', {})
        self._helper.set('execution.execution_path', [])

    def reset_execution_state(self) -> None:
        """Reset execution state to initial values."""
        self._initialize_execution_state()

    def update_execution_node(self, node_id: str, result: Optional[Any] = None) -> None:
        """Update current node and record result.
        
        Args:
            node_id: ID of the node to update to
            result: Optional result from the node execution
        """
        # Update ExecutionState
        self._execution_state.update_node(node_id, result)
        
        # Update context manager state
        current_node_id = self._helper.get('execution.current_node_id')
        if current_node_id:
            path = self._helper.get('execution.execution_path', [])
            path.append((current_node_id, node_id))
            self._helper.set('execution.execution_path', path)
            
        self._helper.set('execution.current_node_id', node_id)
        
        visited_nodes = self._helper.get('execution.visited_nodes', [])
        visited_nodes.append(node_id)
        self._helper.set('execution.visited_nodes', visited_nodes)
        
        if result is not None:
            node_results = self._helper.get('execution.node_results', {})
            node_results[node_id] = result
            self._helper.set('execution.node_results', node_results)

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution history with results.
        
        Returns:
            List of dictionaries containing node IDs and their results
        """
        visited_nodes = self._helper.get('execution.visited_nodes', [])
        node_results = self._helper.get('execution.node_results', {})
        
        return [
            {
                "node_id": node_id,
                "result": node_results.get(node_id)
            }
            for node_id in visited_nodes
        ]

    def get_current_plan_node(self) -> Optional[ExecutionNode]:
        """Get current plan node."""
        if self._current_plan:
            # Assuming Plan object has get_current_node method
            current_node = self._current_plan.get_current_node()
            # Ensure type compatibility if necessary
            if isinstance(current_node, ExecutionNode):
                return current_node
            # Handle cases where get_current_node might return something else or None
            # depending on Plan implementation
        return None
        
    def get_current_reasoning_node(self) -> Optional[ExecutionNode]:
        """Get current reasoning node."""
        if self._current_plan:
            # Assuming Plan object has get_current_reasoning_node method
            current_node = self._current_plan.get_current_reasoning_node()
            if isinstance(current_node, ExecutionNode):
                return current_node
        return None

    def build_llm_context(self) -> Dict[str, Any]:
        """Build context potentially useful for LLM calls.

        Note: The exact context needed varies greatly. This provides a basic structure.
        It retrieves plan/reasoning results assuming they are stored in the 
        transient state via store_node_output under standard keys.
        
        Returns:
            Dictionary containing potentially relevant context.
        """
        plan_node = self.get_current_plan_node()
        reasoning_node = self.get_current_reasoning_node()
        plan_id = plan_node.node_id if plan_node else ""
        
        # --- Retrieve relevant state using the state manager --- 
        
        # Example: Get all transient data (use with caution, might be large)
        # transient_data = self.state.get("temp.")  # Needs manager support for prefix-only get
        # Or get specific keys needed
        current_objective = self._helper.get("temp.objective")  # Assuming objective is stored here

        # Assume results are stored under these keys by store_node_output
        # Adjust keys if storage convention is different
        plan_result_key = f"temp.plan_results.{plan_id}" if plan_id else None
        plan_result = self._helper.get(plan_result_key) if plan_result_key else None

        # Getting all reasoning results for a plan might require iterating or a specific structure
        # Option 1: Assume a single key holds a dict of all reasoning results for the plan
        reasoning_results_key = f"temp.reasoning_results.{plan_id}" if plan_id else None
        all_reasoning_results = self._helper.get(reasoning_results_key, default={}) if reasoning_results_key else {}
        # Option 2: Iterate known reasoning node IDs (if available) - more complex

        llm_context = {
            # Provide specific, relevant transient data instead of the whole context
            # "transient_data": transient_data,
            "current_objective": current_objective,
            "current_step": {
                "plan": plan_node.to_dict() if plan_node else None,
                "reasoning": reasoning_node.to_dict() if reasoning_node else None
            },
            "step_results": {
                "plan": plan_result,
                "reasoning": all_reasoning_results  # Dict of reasoning_id -> result
            },
            # Consider adding relevant agent state if needed by the LLM
            # "user_preferences": self.state.get("agent.user.preferences")
        }
        return llm_context

    def store_node_output(self, node_id: str, result: Any) -> None:
        """Process the output mappings defined in the plan for a given node.
        
        Uses the state manager to store the results.
        
        Args:
            node_id: The ID of the node whose result is being stored.
            result: The structured result dictionary from the node execution.
        """
        if self._current_plan is None:
            log.warning(f"Cannot store output for node '{node_id}', no current_plan in context.")
            # Fallback? Store raw result in transient? Policy decision.
            # self.state.set(f"temp.results.{node_id}", result)
            return

        # Assume Plan object has a method to get the parsed node definition
        node_definition = self._current_plan.get_node_definition(node_id)
        if not node_definition:
            log.warning(f"Node ID '{node_id}' not found in plan definition. Cannot store output.")
            return

        output_mappings = node_definition.get('from_llm', {})  # Get the dictionary
        if not isinstance(output_mappings, dict):
            log.error(f"Invalid 'from_llm' format for node '{node_id}'. Expected dict, got {type(output_mappings)}.")
            return
             
        if not isinstance(result, dict):
            log.warning(f"Cannot process 'from_llm' mappings for node '{node_id}' because result is not a dictionary.")
            # Store raw result? Policy decision.
            # self.state.set(f"temp.results.{node_id}", result)
            return

        for result_field, destination_string in output_mappings.items():
            if not isinstance(destination_string, str):
                # Shortened log message
                log.warning(f"Invalid destination '{destination_string}' for field '{result_field}' in node '{node_id}'. Skipping.")
                continue
                 
            value_to_store = result.get(result_field)
            if value_to_store is None:
                # Check if key actually exists with value None, or if key is missing
                if result_field not in result:
                    # Shortened log message
                    log.warning(f"Field '{result_field}' (from_llm) not in result for node '{node_id}'. Skipping {destination_string}.")
                    continue
                # else: value is legitimately None, proceed to store it
            
            try:
                # Use the state manager's set method
                self._helper.set(destination_string, value_to_store)
            except Exception as e:
                # Log errors from the set operation (already logged in manager, but maybe add context here)
                log.error(f"Failed to store field '{result_field}' to '{destination_string}' for node '{node_id}': {e}")
                # Continue processing other mappings?
                continue
