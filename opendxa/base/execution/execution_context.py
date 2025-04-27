"""Execution context for DXA."""

from typing import Optional, TYPE_CHECKING, Dict, Any, Tuple, cast
from opendxa.base.state.world_state import WorldState
from opendxa.base.resource.base_resource import BaseResource
from opendxa.base.resource.llm_resource import LLMResource
from opendxa.base.execution.execution_types import ExecutionNode
from opendxa.base.state.execution_state import ExecutionState
if TYPE_CHECKING:
    from opendxa.execution.planning import Plan
    from opendxa.execution.reasoning import Reasoning
    from opendxa.base.state import AgentState

class ExecutionContext:
    """Execution context for all execution layers."""

    def __init__(self, 
                 planning_llm: Optional[LLMResource] = None,
                 reasoning_llm: Optional[LLMResource] = None,
                 agent_state: Optional['AgentState'] = None,
                 world_state: Optional[WorldState] = None,
                 execution_state: Optional[ExecutionState] = None,
                 current_plan: Optional['Plan'] = None,
                 current_reasoning: Optional['Reasoning'] = None,
                 global_context: Optional[Dict[str, Any]] = None,
                 available_resources: Optional[Dict[str, BaseResource]] = None
                 ):
        """Initialize execution context.
        
        Args:
            planning_llm: LLM resource for planning
            reasoning_llm: LLM resource for reasoning
            agent_state: Current agent state
            world_state: Current world state
            execution_state: Current execution state
            current_plan: Current plan
            current_reasoning: Current reasoning
            global_context: Global context dictionary
            available_resources: Available resources dictionary
            
        Raises:
            ValueError: If any required resource is invalid
        """
        # State management
        self.agent_state = agent_state
        self.world_state = world_state
        self.execution_state = execution_state
        self.available_resources = available_resources or {}

        # Current execution graphs
        self.current_plan = current_plan
        self.current_reasoning = current_reasoning

        # LLM resources
        self.planning_llm = planning_llm
        self.reasoning_llm = reasoning_llm
        
        # Global context and results storage
        self.global_context = global_context or {}
        self.plan_results: Dict[str, Dict[str, Any]] = {}  # plan_id -> results
        self.reasoning_results: Dict[
            Tuple[str, str],  # (plan_id, reasoning_id)
            Dict[str, Any]
        ] = {}
        
    def get_current_plan_node(self) -> Optional[ExecutionNode]:
        """Get current plan node.
        
        Returns:
            Optional[ExecutionNode]: Current plan node if exists
        """
        if self.current_plan:
            return cast(ExecutionNode, self.current_plan.get_current_node())
        return None
        
    def get_current_reasoning_node(self) -> Optional[ExecutionNode]:
        """Get current reasoning node.
        
        Returns:
            Optional[ExecutionNode]: Current reasoning node if exists
        """
        if self.current_reasoning:
            return cast(ExecutionNode, self.current_reasoning.get_current_node())
        return None

    def update_plan_result(
        self, 
        plan_id: str, 
        result: Dict[str, Any]
    ) -> None:
        """Update results for a plan node.
        
        Args:
            plan_id: ID of the plan
            result: Result dictionary to store
            
        Raises:
            ValueError: If any ID is empty or result is not a dictionary
        """
        if not plan_id:
            raise ValueError("Plan ID cannot be empty")
        if not isinstance(result, dict):
            raise ValueError("Result must be a dictionary")
            
        self.plan_results[plan_id] = result
    
    def update_reasoning_result(
        self, 
        plan_id: str, 
        reasoning_id: str, 
        result: Dict[str, Any]
    ) -> None:
        """Update results for a reasoning node.
        
        Args:
            plan_id: ID of the plan
            reasoning_id: ID of the reasoning
            result: Result dictionary to store
            
        Raises:
            ValueError: If any ID is empty or result is not a dictionary
        """
        if not plan_id or not reasoning_id:
            raise ValueError("Plan ID and Reasoning ID cannot be empty")
        if not isinstance(result, dict):
            raise ValueError("Result must be a dictionary")
            
        self.reasoning_results[(plan_id, reasoning_id)] = result
    
    def get_plan_result(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get results for a specific plan node.
        
        Args:
            plan_id: ID of the plan
            
        Returns:
            Optional[Dict[str, Any]]: Result dictionary if exists
            
        Raises:
            ValueError: If plan_id is empty
        """
        if not plan_id:
            raise ValueError("Plan ID cannot be empty")
        return self.plan_results.get(plan_id)
    
    def get_reasoning_results_for_plan(
        self, 
        plan_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get all reasoning results for a specific plan node.
        
        Args:
            plan_id: ID of the plan
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of reasoning results
            
        Raises:
            ValueError: If plan_id is empty
        """
        if not plan_id:
            raise ValueError("Plan ID cannot be empty")
            
        return {
            reasoning_id: result 
            for (wf_id, p_id, reasoning_id), result in self.reasoning_results.items() 
            if p_id == plan_id
        }
    
    def build_llm_context(self) -> Dict[str, Any]:
        """Build context for LLM call.
        
        Returns:
            Dict[str, Any]: Dictionary containing LLM context
        """
        # Get current workflow and plan IDs safely
        plan_node = self.get_current_plan_node()
        reasoning_node = self.get_current_reasoning_node()
        
        plan_id = plan_node.node_id if plan_node else ""
        
        return {
            "global_context": self.global_context,
            "current": {
                "plan": plan_node.to_dict() if plan_node else None,
                "reasoning": reasoning_node.to_dict() if reasoning_node else None
            },
            "results": {
                "plan": self.get_plan_result(plan_id),
                "reasoning": self.get_reasoning_results_for_plan(plan_id)
            }
        }
