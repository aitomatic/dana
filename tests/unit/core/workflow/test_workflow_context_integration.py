"""
Test workflow context integration with simplified workflow system.

This test file verifies that the simplified workflow system works correctly
with the new design that only supports name, composed_function, and metadata.
"""

from dana.core.workflow import WorkflowInstance, WorkflowType


class TestWorkflowInstanceContextIntegration:
    """Test workflow instance context integration."""

    def test_create_workflow_with_context(self):
        """Test creating a workflow instance with basic context."""
        workflow_type = WorkflowType(
            name="TestWorkflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Test workflow",
        )

        workflow = WorkflowInstance(
            struct_type=workflow_type,
            values={
                "test": "value",
            },
            parent_workflow=None,
        )

        assert workflow.test == "value"
        assert workflow._parent_workflow is None
        assert len(workflow._children) == 0

    def test_create_workflow_with_parent(self):
        """Test creating a workflow instance with parent workflow."""
        parent_type = WorkflowType(
            name="ParentWorkflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Parent workflow",
        )

        parent_workflow = WorkflowInstance(struct_type=parent_type, values={"test": "parent_value"}, parent_workflow=None)

        child_type = WorkflowType(
            name="ChildWorkflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Child workflow",
        )

        child_workflow = WorkflowInstance(struct_type=child_type, values={"test": "child_value"}, parent_workflow=parent_workflow)

        assert child_workflow._parent_workflow == parent_workflow
        assert len(parent_workflow._children) == 1
        assert parent_workflow._children[0] == child_workflow

    def test_workflow_navigation_methods(self):
        """Test workflow navigation methods."""
        # Create a chain of workflows
        root_type = WorkflowType(
            name="RootWorkflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Root workflow",
        )

        root_workflow = WorkflowInstance(struct_type=root_type, values={"test": "root_value"}, parent_workflow=None)

        child1_type = WorkflowType(
            name="Child1Workflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Child 1 workflow",
        )

        child1_workflow = WorkflowInstance(struct_type=child1_type, values={"test": "child1_value"}, parent_workflow=root_workflow)

        child2_type = WorkflowType(
            name="Child2Workflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Child 2 workflow",
        )

        child2_workflow = WorkflowInstance(struct_type=child2_type, values={"test": "child2_value"}, parent_workflow=root_workflow)

        # Test root navigation
        assert child1_workflow.get_root_workflow() == root_workflow
        assert child2_workflow.get_root_workflow() == root_workflow
        assert root_workflow.get_root_workflow() == root_workflow

        # Test sibling navigation
        siblings = child1_workflow.get_sibling_workflows()
        assert len(siblings) == 1
        assert siblings[0] == child2_workflow

        siblings = child2_workflow.get_sibling_workflows()
        assert len(siblings) == 1
        assert siblings[0] == child1_workflow

    def test_workflow_execution_with_action_tracking(self):
        """Test workflow execution with execution history tracking."""
        workflow_type = WorkflowType(
            name="TestWorkflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Test workflow",
        )

        workflow = WorkflowInstance(
            struct_type=workflow_type,
            values={
                "test": "value",
            },
            parent_workflow=None,
        )

        # Test execution history tracking
        assert len(workflow.get_execution_history()) == 0

        step1 = {"action": "step1", "result": "success"}
        workflow.add_execution_step(step1)
        assert len(workflow.get_execution_history()) == 1
        assert workflow.get_execution_history()[0] == step1

        step2 = {"action": "step2", "result": "success"}
        workflow.add_execution_step(step2)
        assert len(workflow.get_execution_history()) == 2
        assert workflow.get_execution_history()[1] == step2

    def test_workflow_execution_error_handling(self):
        """Test workflow execution error handling."""
        workflow_type = WorkflowType(
            name="TestWorkflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Test workflow",
        )

        workflow = WorkflowInstance(
            struct_type=workflow_type,
            values={
                "test": "value",
            },
            parent_workflow=None,
        )

        # Test error handling in execution history
        error_step = {"action": "error_step", "error": "Something went wrong", "status": "failed"}
        workflow.add_execution_step(error_step)

        history = workflow.get_execution_history()
        assert len(history) == 1
        assert history[0]["status"] == "failed"
        assert "error" in history[0]

    def test_workflow_without_action_history(self):
        """Test workflow without action history."""
        workflow_type = WorkflowType(
            name="TestWorkflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Test workflow",
        )

        workflow = WorkflowInstance(
            struct_type=workflow_type,
            values={
                "test": "value",
            },
            parent_workflow=None,
        )

        # Test that workflow works without action history
        assert workflow.test == "value"
        assert len(workflow.get_execution_history()) == 0

    def test_workflow_context_propagation(self):
        """Test workflow context propagation through parent-child relationships."""
        # Create a chain of workflows
        root_type = WorkflowType(
            name="RootWorkflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Root workflow",
        )

        root_workflow = WorkflowInstance(struct_type=root_type, values={"test": "root_value"}, parent_workflow=None)

        child_type = WorkflowType(
            name="ChildWorkflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Child workflow",
        )

        child_workflow = WorkflowInstance(struct_type=child_type, values={"test": "child_value"}, parent_workflow=root_workflow)

        # Test parent-child relationship
        assert child_workflow._parent_workflow == root_workflow
        assert len(root_workflow._children) == 1
        assert root_workflow._children[0] == child_workflow

        # Test ancestor context access (simplified version)
        assert child_workflow.get_ancestor_context(1) is None  # No problem_context in simplified design


class TestWorkflowTypeContextFields:
    """Test workflow type context fields."""

    def test_create_workflow_type_with_context_fields(self):
        """Test creating a workflow type with context fields."""
        workflow_type = WorkflowType(
            name="ContextWorkflow",
            fields={"test": "str"},
            field_order=["test"],
            field_comments={"test": "Test field"},
            field_defaults={"test": "default"},
            docstring="Workflow with context support",
        )

        # Test that default workflow fields are automatically added
        assert "name" in workflow_type.fields
        assert "composed_function" in workflow_type.fields
        assert "metadata" in workflow_type.fields
        assert "test" in workflow_type.fields

        # Test field order includes both custom and default fields
        assert len(workflow_type.field_order) == 4
        assert "test" in workflow_type.field_order
        assert "name" in workflow_type.field_order
        assert "composed_function" in workflow_type.field_order
        assert "metadata" in workflow_type.field_order

        # Test field defaults
        assert workflow_type.field_defaults["test"] == "default"
        assert workflow_type.field_defaults["name"] == "A Workflow"
        assert workflow_type.field_defaults["composed_function"] is None
        assert workflow_type.field_defaults["metadata"] == {}

        # Test field comments
        assert workflow_type.field_comments["test"] == "Test field"
        assert workflow_type.field_comments["name"] == "Name of the workflow"
        assert workflow_type.field_comments["composed_function"] == "The composed function that implements the workflow"
        assert workflow_type.field_comments["metadata"] == "Additional workflow metadata"
