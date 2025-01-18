"""Execution context for DXA."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..state import AgentState, WorldState, ExecutionState
    from ..workflow import Workflow
    from ..planning import Plan
    from ..reasoning import Reasoning
    from ..resource import BaseResource, LLMResource

@dataclass
class ExecutionContext:
    """Context for execution across layers."""

    # State management
    agent_state: Optional['AgentState'] = None
    world_state: Optional['WorldState'] = None
    execution_state: Optional['ExecutionState'] = None

    # Current graphs
    current_workflow: Optional['Workflow'] = None
    current_plan: Optional['Plan'] = None
    current_reasoning: Optional['Reasoning'] = None

    # Resources
    resources: Dict[str, 'BaseResource'] = field(default_factory=dict)  # All available resources

    # Commonly used LLMs
    workflow_llm: Optional['LLMResource'] = None
    planning_llm: Optional['LLMResource'] = None
    reasoning_llm: Optional['LLMResource'] = None

    # Monitoring specific fields
    current_data: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Dict] = field(default_factory=dict)
    fault_patterns: Dict[str, Dict] = field(default_factory=dict)

    def get_resource(self, resource_id: str) -> Optional['BaseResource']:
        """Get resource by ID."""
        return self.resources.get(resource_id)

    def add_resource(self, resource_id: str, resource: 'BaseResource') -> None:
        """Add resource to context."""
        self.resources[resource_id] = resource

    def remove_resource(self, resource_id: str) -> None:
        """Remove resource from context."""
        self.resources.pop(resource_id, None)

    def update_monitoring_data(self, data: Dict[str, Any]) -> None:
        """Update current monitoring data."""
        self.current_data = data

    def check_parameter_limits(self, param_name: str) -> bool:
        """Check if parameter is within normal range."""
        if not self.parameters or param_name not in self.current_data.get("values", {}):
            return True  # Default to normal if no data

        param_value = self.current_data["values"][param_name]
        param_def = self.parameters.get("rf_matching", {}).get(param_name, {})

        if not param_def or "normal_range" not in param_def:
            return True

        normal_min, normal_max = param_def["normal_range"]
        return normal_min <= param_value <= normal_max

    def check_conditions(self, condition: str) -> bool:
        """Check monitoring conditions."""
        if condition == "parameters_normal":
            # Check all parameters are within limits
            return all(
                self.check_parameter_limits(param)
                for param in self.current_data.get("values", {})
            )
        elif condition == "parameters_abnormal":
            # Check if any parameter is outside limits
            return not self.check_conditions("parameters_normal")

        return False  # Unknown condition
