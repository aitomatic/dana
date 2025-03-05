"""Execution context for DXA."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, TYPE_CHECKING, cast
from .execution_types import ExecutionNode
if TYPE_CHECKING:
    from ..agent import AgentState, WorldState, ExecutionState
    from ..agent.resource import LLMResource
    from .workflow import Workflow
    from .planning import Plan
    from .reasoning import Reasoning

@dataclass
class ExecutionContext:
    """Execution context for all execution layers."""

    # State management
    agent_state: Optional['AgentState'] = None
    world_state: Optional['WorldState'] = None
    execution_state: Optional['ExecutionState'] = None

    # Current execution graphs
    current_workflow: Optional['Workflow'] = None
    current_plan: Optional['Plan'] = None
    current_reasoning: Optional['Reasoning'] = None

    # LLM resources
    workflow_llm: Optional['LLMResource'] = None
    planning_llm: Optional['LLMResource'] = None
    reasoning_llm: Optional['LLMResource'] = None

    def __init__(self, 
                 workflow_llm: 'LLMResource',
                 planning_llm: 'LLMResource',
                 reasoning_llm: 'LLMResource',
                 agent_state: Optional['AgentState'] = None,
                 world_state: Optional['WorldState'] = None,
                 execution_state: Optional['ExecutionState'] = None,
                 current_workflow: Optional['Workflow'] = None,
                 current_plan: Optional['Plan'] = None,
                 current_reasoning: Optional['Reasoning'] = None
                 ):
        """Initialize execution context."""
        self.agent_state = agent_state
        self.world_state = world_state
        self.execution_state = execution_state

        self.current_workflow = current_workflow
        self.current_plan = current_plan
        self.current_reasoning = current_reasoning

        self.workflow_llm = workflow_llm or planning_llm or reasoning_llm
        self.planning_llm = planning_llm or reasoning_llm
        self.reasoning_llm = reasoning_llm
        
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
        
    # TODO: remove/refactor
    def _deprecated_update_monitoring_data(self, data: Dict[str, Any]) -> None:
        """Update current monitoring data."""
        self.current_data = data

    # TODO: remove/refactor
    def _deprecated_check_parameter_limits(self, param_name: str) -> bool:
        """Check if parameter is within normal range."""
        if not self.parameters or param_name not in self.current_data.get("values", {}):
            return True

        param_value = self.current_data["values"][param_name]
        param_def = self.parameters.get("rf_matching", {}).get(param_name, {})

        if not param_def or "normal_range" not in param_def:
            return True

        normal_min, normal_max = param_def["normal_range"]
        return normal_min <= param_value <= normal_max

    # TODO: remove/refactor
    def _deprecated_check_conditions(self, condition: str) -> bool:
        """Check monitoring conditions."""
        if condition == "parameters_normal":
            return all(
                self.check_parameter_limits(param)
                for param in self.current_data.get("values", {})
            )
        elif condition == "parameters_abnormal":
            return not self.check_conditions("parameters_normal")

        return False  # Unknown condition
