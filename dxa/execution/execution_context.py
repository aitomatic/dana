"""Execution context for DXA."""

from typing import Optional, TYPE_CHECKING, cast, Dict, Any, Tuple

from dxa.agent.resource.base_resource import BaseResource
from .execution_types import ExecutionNode
if TYPE_CHECKING:
    from ..agent import AgentState, WorldState, ExecutionState
    from ..agent.resource import LLMResource
    from .workflow import Workflow
    from .planning import Plan
    from .reasoning import Reasoning

class ExecutionContext:
    """Execution context for all execution layers."""

    def __init__(self, 
                 workflow_llm: 'LLMResource',
                 planning_llm: 'LLMResource',
                 reasoning_llm: 'LLMResource',
                 agent_state: Optional['AgentState'] = None,
                 world_state: Optional['WorldState'] = None,
                 execution_state: Optional['ExecutionState'] = None,
                 current_workflow: Optional['Workflow'] = None,
                 current_plan: Optional['Plan'] = None,
                 current_reasoning: Optional['Reasoning'] = None,
                 global_context: Optional[Dict[str, Any]] = None,
                 resources: Optional[Dict[str, BaseResource]] = None
                 ):
        """Initialize execution context."""
        # State management
        self.agent_state = agent_state
        self.world_state = world_state
        self.execution_state = execution_state
        self.resources = resources

        # Current execution graphs
        self.current_workflow = current_workflow
        self.current_plan = current_plan
        self.current_reasoning = current_reasoning

        # LLM resources
        self.workflow_llm = workflow_llm or planning_llm or reasoning_llm
        self.planning_llm = planning_llm or reasoning_llm
        self.reasoning_llm = reasoning_llm
        
        # Global context and results storage
        self.global_context = global_context or {}
        self.workflow_results: Dict[str, Dict[str, Any]] = {}  # node_id -> results
        self.plan_results: Dict[Tuple[str, str], Dict[str, Any]] = {}  # (workflow_id, plan_id) -> results
        self.reasoning_results: Dict[
            Tuple[str, str, str],  # (workflow_id, plan_id, reasoning_id)
            Dict[str, Any]
        ] = {}
        
    def get_current_workflow_node(self) -> Optional[ExecutionNode]:
        """Get the current workflow node."""
        if self.current_workflow:
            return cast(ExecutionNode, self.current_workflow.get_current_node())
        return None
    
    def get_current_plan_node(self) -> Optional[ExecutionNode]:
        """Get current plan node."""
        if self.current_plan:
            return cast(ExecutionNode, self.current_plan.get_current_node())
        return None
        
    def get_current_reasoning_node(self) -> Optional[ExecutionNode]:
        """Get current reasoning node."""
        if self.current_reasoning:
            return cast(ExecutionNode, self.current_reasoning.get_current_node())
        return None

    def update_workflow_result(self, node_id: str, result: Dict[str, Any]) -> None:
        """Update results for a workflow node."""
        self.workflow_results[node_id] = result
    
    def update_plan_result(
        self, 
        workflow_id: str, 
        plan_id: str, 
        result: Dict[str, Any]
    ) -> None:
        """Update results for a plan node."""
        self.plan_results[(workflow_id, plan_id)] = result
    
    def update_reasoning_result(
        self, 
        workflow_id: str, 
        plan_id: str, 
        reasoning_id: str, 
        result: Dict[str, Any]
    ) -> None:
        """Update results for a reasoning node."""
        self.reasoning_results[(workflow_id, plan_id, reasoning_id)] = result
    
    def get_workflow_result(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get results for a specific workflow node."""
        return self.workflow_results.get(node_id)
    
    def get_plan_results_for_workflow(self, workflow_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all plan results for a specific workflow node."""
        return {
            plan_id: result 
            for (wf_id, plan_id), result in self.plan_results.items() 
            if wf_id == workflow_id
        }
    
    def get_reasoning_results_for_plan(
        self, 
        workflow_id: str, 
        plan_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get all reasoning results for a specific plan node."""
        return {
            reasoning_id: result 
            for (wf_id, p_id, reasoning_id), result in self.reasoning_results.items() 
            if wf_id == workflow_id and p_id == plan_id
        }
    
    def build_llm_context(self) -> Dict[str, Any]:
        """Build context for LLM call."""
        # Get current workflow and plan IDs safely
        workflow_node = self.get_current_workflow_node()
        plan_node = self.get_current_plan_node()
        reasoning_node = self.get_current_reasoning_node()
        
        workflow_id = workflow_node.node_id if workflow_node else ""
        plan_id = plan_node.node_id if plan_node else ""
        
        return {
            "global_context": self.global_context,
            "current": {
                "workflow": workflow_node.to_dict() if workflow_node else None,
                "plan": plan_node.to_dict() if plan_node else None,
                "reasoning": reasoning_node.to_dict() if reasoning_node else None
            },
            "results": {
                "workflow": self.workflow_results,
                "plan": self.get_plan_results_for_workflow(workflow_id),
                "reasoning": self.get_reasoning_results_for_plan(workflow_id, plan_id)
            }
        }
