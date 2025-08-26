"""
Workflow Factory for Dana

Factory for creating WorkflowInstance objects from textual YAML definitions.
Supports automatic FSM generation and workflow validation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dataclasses import dataclass, field
from typing import Any

import yaml

from dana.builtin_types.workflow.workflow_system import WorkflowInstance, WorkflowType


@dataclass
class WorkflowStep:
    """Individual workflow step definition."""

    id: str
    name: str
    action: str
    objective: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    conditions: dict[str, Any] = field(default_factory=dict)
    next_step: str | None = None
    error_step: str | None = None


@dataclass
class WorkflowDefinition:
    """Structured workflow definition from parsed YAML."""

    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    fsm_config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    original_yaml: str = ""  # Preserve the original YAML text

    def to_workflow_type(self) -> WorkflowType:
        """Convert to WorkflowType."""
        fields = {}
        field_order = []
        field_defaults = {}
        field_comments = {}

        # Add original_yaml field to preserve the source YAML
        fields["original_yaml"] = "str"
        field_order.append("original_yaml")
        field_defaults["original_yaml"] = self.original_yaml
        field_comments["original_yaml"] = "Original YAML workflow definition"

        return WorkflowType(
            name=self.name,
            fields=fields,
            field_order=field_order,
            field_defaults=field_defaults,
            field_comments=field_comments,
            docstring=self.description,
        )

    def to_workflow_instance(self) -> WorkflowInstance:
        """Convert to WorkflowInstance."""
        workflow_type = self.to_workflow_type()

        # Create initial values
        values = {
            "name": self.name,
            "fsm": None,  # Will be set by WorkflowInstance constructor
        }

        # Add original_yaml field
        values["original_yaml"] = self.original_yaml

        # Create workflow instance
        workflow_instance = WorkflowInstance(workflow_type, values)

        # Create enhanced FSM with state metadata and workflow metadata
        workflow_instance.fsm = self._create_enhanced_fsm()

        return workflow_instance

    def _create_enhanced_fsm(self) -> Any:
        """Create enhanced FSM with state metadata and workflow metadata."""
        from dana.builtin_types.workflow.workflow_system import create_fsm_instance

        # Create workflow metadata
        workflow_metadata = {
            "name": self.name,
            "description": self.description,
            "total_steps": len(self.steps),
            "fsm_config": self.fsm_config,
        }

        # Create state metadata from steps
        state_metadata = {}
        states = ["START"]

        for step in self.steps:
            state_name = f"STEP_{step.id}"
            states.append(state_name)
            state_metadata[state_name] = {
                "action": step.action,
                "objective": step.objective,
                "parameters": step.parameters or {},
                "conditions": step.conditions or {},
                "status": "pending",
            }

        states.append("COMPLETE")

        # Create transitions
        transitions = {}
        for i in range(len(states) - 1):
            from_state = states[i]
            to_state = states[i + 1]
            transitions[f"{from_state}:next"] = to_state

        # Add error transitions if specified
        for step in self.steps:
            if step.error_step:
                state_name = f"STEP_{step.id}"
                error_state = f"STEP_{step.error_step}"
                transitions[f"{state_name}:error"] = error_state

        # Create FSM data
        fsm_data = {
            "states": states,
            "initial_state": "START",
            "current_state": "START",
            "transitions": transitions,
            "state_metadata": state_metadata,
            "results": {},
            "workflow_metadata": workflow_metadata,
        }

        return create_fsm_instance(fsm_data)


class YAMLWorkflowParser:
    """Parse YAML workflow definitions."""

    def parse(self, text: str) -> WorkflowDefinition:
        """Parse YAML text into WorkflowDefinition."""
        try:
            # Extract YAML content if wrapped in code blocks
            yaml_text = self._extract_yaml_content(text)

            # Parse YAML
            data = yaml.safe_load(yaml_text)

            # Validate structure
            if not self._validate_yaml_structure(data):
                raise ValueError("Invalid YAML workflow structure")

            # Convert to WorkflowDefinition, preserving original text
            return self._convert_to_workflow_definition(data, text)

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse workflow: {e}")

    def _extract_yaml_content(self, text: str) -> str:
        """Extract YAML content from text, handling code blocks."""
        text = text.strip()

        # Remove YAML code block markers
        if text.startswith("```yaml"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    def _validate_yaml_structure(self, data: dict[str, Any]) -> bool:
        """Validate YAML workflow structure."""
        if not isinstance(data, dict):
            return False

        # Check for required workflow key
        if "workflow" not in data:
            return False

        workflow = data["workflow"]
        if not isinstance(workflow, dict):
            return False

        # Check for required name
        if "name" not in workflow:
            return False

        # Check for steps (optional but common)
        if "steps" in workflow and not isinstance(workflow["steps"], list):
            return False

        return True

    def _convert_to_workflow_definition(self, data: dict[str, Any], original_text: str) -> WorkflowDefinition:
        """Convert parsed YAML data to WorkflowDefinition."""
        workflow_data = data["workflow"]

        # Extract basic info
        name = workflow_data["name"]
        description = workflow_data.get("description", "")

        # Parse steps
        steps = []
        if "steps" in workflow_data:
            steps = self._parse_steps(workflow_data["steps"])

        # Parse FSM config if present
        fsm_config = workflow_data.get("fsm", {})

        # Parse metadata
        metadata = workflow_data.get("metadata", {})

        return WorkflowDefinition(
            name=name, description=description, steps=steps, fsm_config=fsm_config, metadata=metadata, original_yaml=original_text
        )

    def _parse_steps(self, steps_data: list[dict[str, Any]]) -> list[WorkflowStep]:
        """Parse workflow steps from YAML data."""
        steps = []

        for i, step_data in enumerate(steps_data):
            # Generate step ID if not provided
            step_id = step_data.get("id", f"step_{i + 1}")

            # Extract step information
            step = WorkflowStep(
                id=step_id,
                name=step_data.get("name", step_data.get("action", f"Step {i + 1}")),
                action=step_data.get("action", ""),
                objective=step_data.get("objective", ""),
                parameters=step_data.get("parameters", {}),
                conditions=step_data.get("conditions", {}),
                next_step=step_data.get("next_step"),
                error_step=step_data.get("error_step"),
            )

            steps.append(step)

        return steps


class WorkflowFactory:
    """Factory for creating WorkflowInstance from textual definitions."""

    def __init__(self):
        self._yaml_parser = YAMLWorkflowParser()

    def create_from_text(self, text: str, format_type: str = "yaml") -> WorkflowInstance:
        """Create WorkflowInstance from textual definition."""
        if format_type.lower() == "yaml":
            return self.create_from_yaml(text)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    def create_from_yaml(self, yaml_text: str) -> WorkflowInstance:
        """Create workflow from YAML definition."""
        # Parse YAML to WorkflowDefinition
        workflow_def = self._yaml_parser.parse(yaml_text)

        # Convert to WorkflowInstance
        return workflow_def.to_workflow_instance()

    def create_simple_workflow(self, name: str, steps: list[str], description: str = "") -> WorkflowInstance:
        """Create a simple linear workflow from step names."""
        # Convert step names to WorkflowStep objects
        workflow_steps = []
        for i, step_name in enumerate(steps):
            step = WorkflowStep(
                id=f"step_{i + 1}", name=step_name, action=step_name.lower().replace(" ", "_"), objective=f"Execute {step_name}"
            )
            workflow_steps.append(step)

        # Create workflow definition with generated YAML
        workflow_def = WorkflowDefinition(
            name=name,
            description=description,
            steps=workflow_steps,
            original_yaml=self._generate_simple_workflow_yaml(name, description, steps),
        )

        return workflow_def.to_workflow_instance()

    def _generate_simple_workflow_yaml(self, name: str, description: str, steps: list[str]) -> str:
        """Generate YAML representation of a simple workflow."""
        yaml_lines = ["workflow:", f'  name: "{name}"', f'  description: "{description}"', "  steps:"]

        for i, step_name in enumerate(steps, 1):
            yaml_lines.extend(
                [f"    - step: {i}", f'      action: "{step_name.lower().replace(" ", "_")}"', f'      objective: "Execute {step_name}"']
            )

        return "\n".join(yaml_lines)

    def validate_workflow_text(self, text: str, format_type: str = "yaml") -> bool:
        """Validate workflow text without creating instance."""
        try:
            if format_type.lower() == "yaml":
                self._yaml_parser.parse(text)
                return True
            else:
                return False
        except Exception:
            return False
