from typing import Any

from dana.common import SandboxContext

from .agent_instance import AgentInstance, AgentType, register_agent_type


class GeneralSolver(AgentInstance):
    def __init__(self, struct_type: AgentType, values: dict[str, Any]):
        super().__init__(struct_type, values)
        # Add custom initialization
        self._custom_state = {}

    def custom_method(self, sandbox_context: SandboxContext, param: str) -> Any:
        """Custom method specific to this agent type."""
        return f"Custom processing: {param}"

    def plan(self, sandbox_context: SandboxContext, task: str, context: dict | None = None) -> Any:
        """Override the default plan method with custom logic."""
        # Custom planning logic
        custom_plan = f"Custom plan for: {task}"

        # Still call parent if needed
        parent_result = super().plan(sandbox_context, task, context)

        return f"{custom_plan} + {parent_result}"


_custom_agent_type = AgentType(
    name="GeneralSolver",
    fields={"custom_field": "str"},
    field_order=["custom_field"],
    field_defaults={"custom_field": "default_value"},
    field_comments={},
)

# Register the type
register_agent_type(_custom_agent_type)


# Define custom method
def _custom_plan_method(agent_instance: AgentInstance, sandbox_context: SandboxContext, task: str, context: dict | None = None) -> Any:
    return f"Custom planning for: {task} with domain: {agent_instance.domain}"


_custom_agent_type.add_agent_method("plan", _custom_plan_method)


# Dana side - use the custom agent
# general_solver = GeneralSolver(custom_agent_type, {"custom_field": "value"})
# result = general_solver.custom_method(context, "test")
