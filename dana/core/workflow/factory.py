"""
Workflow Factory for Dana

This module provides factory functions for creating workflows from YAML definitions
and other sources, working with the ComposedFunction-based workflow system.
"""

import yaml

from .workflow_system import WorkflowInstance, WorkflowType


class WorkflowStep:
    """Represents a single step in a workflow."""

    def __init__(self, step: int = None, action: str = "", objective: str = "", **kwargs):
        # Handle case where step might be passed as a keyword argument
        if step is None and "id" in kwargs:
            step = kwargs.pop("id")
        elif step is None:
            step = 1

        # Handle case where action might be passed as a different key
        if not action and "name" in kwargs:
            action = kwargs.pop("name")

        self.step = step
        self.action = action
        self.objective = objective

        # Store name if provided
        if "name" in kwargs:
            self.name = kwargs.pop("name")
        else:
            self.name = action

        # Store id if provided, otherwise derive from step
        if "id" in kwargs:
            self._id = kwargs.pop("id")
        else:
            # Only derive from step if step is a number
            if isinstance(self.step, int):
                self._id = f"step_{self.step}"
            else:
                self._id = str(self.step)

        # Store additional attributes
        self.parameters = kwargs.pop("parameters", {})
        self.conditions = kwargs.pop("conditions", {})
        self.next_step = kwargs.pop("next_step", None)
        self.error_step = kwargs.pop("error_step", None)

        self.extra_data = kwargs

    @property
    def id(self) -> str:
        """Get the step identifier."""
        return self._id


class WorkflowDefinition:
    """Represents a parsed workflow definition from YAML."""

    def __init__(self, name: str, description: str, steps: list[WorkflowStep], **kwargs):
        self.name = name
        self.description = description
        self.steps = steps

        # Extract common attributes
        self.fsm_config = kwargs.pop("fsm", kwargs.pop("fsm_config", {}))
        self.metadata = kwargs.pop("metadata", {})

        self.extra_data = kwargs

    def to_workflow_type(self) -> WorkflowType:
        """Convert to a WorkflowType."""
        # Create fields based on steps
        fields = {}
        field_order = []
        field_defaults = {}
        field_comments = {}

        for step in self.steps:
            # Use the step's id if it's a simple step number, otherwise use the id directly
            if step.id.startswith("step_") and step.id[5:].isdigit():
                step_field = step.id
            else:
                step_field = f"step_{step.step}"
            fields[step_field] = "str"
            field_order.append(step_field)
            field_defaults[step_field] = "pending"
            field_comments[step_field] = f"Status of step {step.step}: {step.objective}"

        # Add result field
        fields["result"] = "dict"
        field_order.append("result")
        field_defaults["result"] = {}
        field_comments["result"] = "Workflow execution results"

        return WorkflowType(
            name=self.name,
            fields=fields,
            field_order=field_order,
            field_defaults=field_defaults,
            field_comments=field_comments,
            docstring=self.description,
        )

    def to_workflow_instance(self) -> WorkflowInstance:
        """Convert to a WorkflowInstance."""
        workflow_type = self.to_workflow_type()

        # Create initial values including required default fields
        values = {
            "name": self.name,
            "composed_function": None,  # Required by workflow system
            "metadata": {"description": self.description, "steps": len(self.steps)},
        }

        # Add step fields
        for step in self.steps:
            # Use the same field naming logic as to_workflow_type
            if step.id.startswith("step_") and step.id[5:].isdigit():
                step_field = step.id
            else:
                step_field = f"step_{step.step}"
            values[step_field] = "pending"
        values["result"] = {}

        return WorkflowInstance(workflow_type, values)


class YAMLWorkflowParser:
    """Parser for YAML workflow definitions."""

    def parse(self, yaml_text: str) -> WorkflowDefinition:
        """Parse YAML text into a WorkflowDefinition."""
        # Strip markdown code blocks if present
        cleaned_yaml = yaml_text.strip()
        if cleaned_yaml.startswith("```") and cleaned_yaml.endswith("```"):
            # Extract content between code blocks
            lines = cleaned_yaml.split("\n")
            if len(lines) >= 3:
                # Skip first line (```yaml) and last line (```)
                content_lines = lines[1:-1]
                cleaned_yaml = "\n".join(content_lines)

        try:
            data = yaml.safe_load(cleaned_yaml)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")

        if "workflow" not in data:
            raise ValueError("Missing 'workflow' key in YAML")

        workflow_data = data["workflow"]
        name = workflow_data.get("name")
        if not name:
            raise ValueError("Missing workflow name")
        description = workflow_data.get("description", "")
        steps_data = workflow_data.get("steps", [])

        steps = []
        for step_data in steps_data:
            step = WorkflowStep(
                step=step_data.get("step", len(steps) + 1),
                action=step_data.get("action", ""),
                objective=step_data.get("objective", ""),
                **{k: v for k, v in step_data.items() if k not in ["step", "action", "objective"]},
            )
            steps.append(step)

        # Filter out keys that are already handled as positional arguments
        extra_data = {k: v for k, v in workflow_data.items() if k not in ["name", "description", "steps"]}
        return WorkflowDefinition(name, description, steps, **extra_data)


class WorkflowFactory:
    """Factory for creating workflows from various sources."""

    def __init__(self):
        self.parser = YAMLWorkflowParser()

    def create_from_yaml(self, yaml_text: str) -> WorkflowInstance:
        """Create a workflow from YAML text."""
        workflow_def = self.parser.parse(yaml_text)
        return workflow_def.to_workflow_instance()

    def create_simple_workflow(self, name: str, steps: list[str], description: str, objective: str) -> WorkflowInstance:
        """Create a simple workflow from step names."""
        workflow_steps = []
        for i, step_name in enumerate(steps, 1):
            workflow_steps.append(WorkflowStep(step=i, action=step_name, objective=objective))

        workflow_def = WorkflowDefinition(name, description, workflow_steps)
        return workflow_def.to_workflow_instance()

    def validate_workflow_text(self, yaml_text: str) -> bool:
        """Validate that YAML text represents a valid workflow."""
        try:
            self.parser.parse(yaml_text)
            return True
        except (ValueError, yaml.YAMLError):
            return False
