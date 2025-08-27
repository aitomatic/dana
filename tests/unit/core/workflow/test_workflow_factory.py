"""
Unit tests for WorkflowFactory.

Tests the creation of WorkflowInstance objects from YAML text.
"""

import pytest

from dana.builtin_types.workflow.factory import WorkflowFactory, YAMLWorkflowParser, WorkflowDefinition, WorkflowStep


class TestWorkflowFactory:
    """Test WorkflowFactory functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = WorkflowFactory()
        self.parser = YAMLWorkflowParser()

        # Sample valid YAML workflow
        self.valid_yaml = """
workflow:
  name: "TestWorkflow"
  description: "A test workflow"
  steps:
    - step: 1
      action: "test_action"
      objective: "Test objective"
"""

    def test_create_from_yaml_valid(self):
        """Test creating workflow from valid YAML."""
        workflow = self.factory.create_from_yaml(self.valid_yaml)

        assert workflow is not None
        assert workflow.name == "TestWorkflow"
        assert workflow.get_status() == "created"
        assert hasattr(workflow, "fsm")

    def test_create_from_yaml_invalid(self):
        """Test creating workflow from invalid YAML."""
        invalid_yaml = "invalid: yaml: content"

        with pytest.raises(ValueError):
            self.factory.create_from_yaml(invalid_yaml)

    def test_create_from_yaml_missing_workflow_key(self):
        """Test creating workflow from YAML missing workflow key."""
        invalid_yaml = """
name: "TestWorkflow"
description: "A test workflow"
"""

        with pytest.raises(ValueError):
            self.factory.create_from_yaml(invalid_yaml)

    def test_create_simple_workflow(self):
        """Test creating simple workflow from step names."""
        steps = ["Step 1", "Step 2", "Step 3"]
        workflow = self.factory.create_simple_workflow("SimpleWorkflow", steps, "Test description", "Test objective")

        assert workflow is not None
        assert workflow.name == "SimpleWorkflow"
        assert workflow.get_status() == "created"

    def test_validate_workflow_text_valid(self):
        """Test workflow text validation with valid YAML."""
        is_valid = self.factory.validate_workflow_text(self.valid_yaml)
        assert is_valid is True

    def test_validate_workflow_text_invalid(self):
        """Test workflow text validation with invalid YAML."""
        invalid_yaml = "invalid: yaml: content"
        is_valid = self.factory.validate_workflow_text(invalid_yaml)
        assert is_valid is False


class TestYAMLWorkflowParser:
    """Test YAMLWorkflowParser functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = YAMLWorkflowParser()

        self.valid_yaml = """
workflow:
  name: "TestWorkflow"
  description: "A test workflow"
  steps:
    - step: 1
      action: "test_action"
      objective: "Test objective"
    - step: 2
      action: "another_action"
      objective: "Another objective"
"""

    def test_parse_valid_yaml(self):
        """Test parsing valid YAML."""
        workflow_def = self.parser.parse(self.valid_yaml)

        assert isinstance(workflow_def, WorkflowDefinition)
        assert workflow_def.name == "TestWorkflow"
        assert workflow_def.description == "A test workflow"
        assert len(workflow_def.steps) == 2

        # Check first step
        step1 = workflow_def.steps[0]
        assert step1.id == "step_1"
        assert step1.action == "test_action"
        assert step1.objective == "Test objective"

        # Check second step
        step2 = workflow_def.steps[1]
        assert step2.id == "step_2"
        assert step2.action == "another_action"
        assert step2.objective == "Another objective"

    def test_parse_yaml_with_code_blocks(self):
        """Test parsing YAML wrapped in code blocks."""
        yaml_with_blocks = f"```yaml\n{self.valid_yaml}\n```"
        workflow_def = self.parser.parse(yaml_with_blocks)

        assert workflow_def.name == "TestWorkflow"
        assert len(workflow_def.steps) == 2

    def test_parse_yaml_with_custom_fsm(self):
        """Test parsing YAML with custom FSM configuration."""
        yaml_with_fsm = """
workflow:
  name: "FSMWorkflow"
  description: "Workflow with custom FSM"
  steps:
    - step: 1
      action: "start"
      objective: "Start the workflow"
  fsm:
    type: "linear"
    states: ["START", "PROCESSING", "COMPLETE"]
"""

        workflow_def = self.parser.parse(yaml_with_fsm)

        assert workflow_def.name == "FSMWorkflow"
        assert workflow_def.fsm_config["type"] == "linear"
        assert workflow_def.fsm_config["states"] == ["START", "PROCESSING", "COMPLETE"]

    def test_parse_yaml_with_metadata(self):
        """Test parsing YAML with metadata."""
        yaml_with_metadata = """
workflow:
  name: "MetadataWorkflow"
  description: "Workflow with metadata"
  steps:
    - step: 1
      action: "test"
      objective: "Test"
  metadata:
    version: "1.0"
    author: "Test Author"
    tags: ["test", "workflow"]
"""

        workflow_def = self.parser.parse(yaml_with_metadata)

        assert workflow_def.name == "MetadataWorkflow"
        assert workflow_def.metadata["version"] == "1.0"
        assert workflow_def.metadata["author"] == "Test Author"
        assert workflow_def.metadata["tags"] == ["test", "workflow"]

    def test_parse_invalid_yaml(self):
        """Test parsing invalid YAML."""
        invalid_yaml = "invalid: yaml: content: ["

        with pytest.raises(ValueError):
            self.parser.parse(invalid_yaml)

    def test_parse_missing_workflow_key(self):
        """Test parsing YAML missing workflow key."""
        invalid_yaml = """
name: "TestWorkflow"
description: "A test workflow"
"""

        with pytest.raises(ValueError):
            self.parser.parse(invalid_yaml)

    def test_parse_missing_name(self):
        """Test parsing YAML missing workflow name."""
        invalid_yaml = """
workflow:
  description: "A test workflow"
  steps:
    - step: 1
      action: "test"
"""

        with pytest.raises(ValueError):
            self.parser.parse(invalid_yaml)


class TestWorkflowDefinition:
    """Test WorkflowDefinition functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.steps = [
            WorkflowStep(id="step_1", name="Test Step 1", action="test_action_1", objective="Test objective 1"),
            WorkflowStep(id="step_2", name="Test Step 2", action="test_action_2", objective="Test objective 2"),
        ]

        self.workflow_def = WorkflowDefinition(name="TestWorkflow", description="A test workflow", steps=self.steps)

    def test_to_workflow_type(self):
        """Test converting to WorkflowType."""
        workflow_type = self.workflow_def.to_workflow_type()

        assert workflow_type.name == "TestWorkflow"
        assert workflow_type.docstring == "A test workflow"

        # Check that step fields were created
        assert "step_step_1" in workflow_type.fields
        assert "step_step_2" in workflow_type.fields
        assert "result" in workflow_type.fields

        # Check field defaults
        assert workflow_type.field_defaults["step_step_1"] == "pending"
        assert workflow_type.field_defaults["step_step_2"] == "pending"
        assert workflow_type.field_defaults["result"] == {}

    def test_to_workflow_instance(self):
        """Test converting to WorkflowInstance."""
        workflow_instance = self.workflow_def.to_workflow_instance()

        assert workflow_instance.name == "TestWorkflow"
        assert workflow_instance.get_status() == "created"
        assert hasattr(workflow_instance, "fsm")

        # Check that step status fields were created
        assert hasattr(workflow_instance, "step_step_1")
        assert hasattr(workflow_instance, "step_step_2")
        assert hasattr(workflow_instance, "result")

        # Check initial values
        assert workflow_instance.step_step_1 == "pending"
        assert workflow_instance.step_step_2 == "pending"
        assert workflow_instance.result == {}

    def test_to_workflow_instance_with_custom_fsm(self):
        """Test converting to WorkflowInstance with custom FSM."""
        workflow_def = WorkflowDefinition(
            name="FSMWorkflow",
            description="Workflow with custom FSM",
            steps=self.steps,
            fsm_config={"type": "linear", "states": ["START", "PROCESSING", "COMPLETE"]},
        )

        workflow_instance = workflow_def.to_workflow_instance()

        assert workflow_instance.name == "FSMWorkflow"
        assert workflow_instance.fsm is not None
        # Note: We can't easily test the FSM content without more complex setup


class TestWorkflowStep:
    """Test WorkflowStep functionality."""

    def test_workflow_step_creation(self):
        """Test creating WorkflowStep."""
        step = WorkflowStep(
            id="test_step",
            name="Test Step",
            action="test_action",
            objective="Test objective",
            parameters={"param1": "value1"},
            conditions={"condition1": True},
        )

        assert step.id == "test_step"
        assert step.name == "Test Step"
        assert step.action == "test_action"
        assert step.objective == "Test objective"
        assert step.parameters == {"param1": "value1"}
        assert step.conditions == {"condition1": True}

    def test_workflow_step_defaults(self):
        """Test WorkflowStep with default values."""
        step = WorkflowStep(id="test_step", name="Test Step", action="test_action")

        assert step.objective == ""
        assert step.parameters == {}
        assert step.conditions == {}
        assert step.next_step is None
        assert step.error_step is None


if __name__ == "__main__":
    pytest.main([__file__])
