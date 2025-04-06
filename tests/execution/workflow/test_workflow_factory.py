"""Test workflow factory."""

import unittest
from opendxa.execution import WorkflowFactory
from opendxa.execution import ExecutionNodeStatus
from opendxa.common.graph import NodeType
from opendxa.execution import Workflow
from opendxa.execution import Objective

class TestWorkflowFactory(unittest.TestCase):
    """Test workflow factory."""

    def test_create_workflow(self):
        """Test creating a basic workflow."""
        objective = Objective("Test objective")
        workflow = WorkflowFactory.create_workflow(objective, name="test_workflow")
        
        assert isinstance(workflow, Workflow)
        assert workflow.objective == objective
        assert workflow.name == "test_workflow"

    def test_create_workflow_by_name(self):
        """Test creating a workflow with a named configuration."""
        objective = Objective("Test objective")
        workflow = WorkflowFactory.create_workflow_by_name(
            "default",
            objective,
            role="Test Role",
            custom_prompts={"task": "Custom task prompt"}
        )
        
        assert isinstance(workflow, Workflow)
        assert workflow.objective == objective
        assert workflow.metadata.get("role") == "Test Role"
        assert workflow.metadata.get("prompts", {}).get("task") == "Custom task prompt"

    def test_create_default_workflow(self):
        """Test creating a default workflow."""
        objective = "Test default workflow"
        workflow = WorkflowFactory.create_default_workflow(objective)
        
        assert isinstance(workflow, Workflow)
        assert workflow.objective is not None
        assert workflow.objective.current == objective
        
        # Verify nodes exist and are connected correctly
        assert "START" in workflow.nodes
        assert "TASK" in workflow.nodes
        assert "END" in workflow.nodes
        
        # Verify node types
        assert workflow.nodes["START"].node_type == NodeType.START
        assert workflow.nodes["TASK"].node_type == NodeType.TASK
        assert workflow.nodes["END"].node_type == NodeType.END
        
        # Verify edges
        edges = workflow.edges
        assert len(edges) == 2
        assert any(e.source == "START" and e.target == "TASK" for e in edges)
        assert any(e.source == "TASK" and e.target == "END" for e in edges)

    def test_create_basic_workflow(self):
        """Test creating a basic workflow with sequential tasks."""
        objective = "Test Objective"
        commands = ["First Task", "Second Task"]

        workflow = WorkflowFactory.create_basic_workflow(objective, commands)

        # Assertions
        self.assertEqual(len(workflow.nodes), 4, "Workflow should have 4 nodes (including START and END)")
        self.assertEqual(len(workflow.edges), 3, "Workflow should have 3 edges")

        # Check node types and descriptions
        self._get_step_and_assert_type(workflow, "START", NodeType.START)
        self._get_step_and_assert_type(workflow, "TASK_0", NodeType.TASK)
        self._get_step_and_assert_type(workflow, "TASK_1", NodeType.TASK)
        self._get_step_and_assert_type(workflow, "END", NodeType.END)

        # Check node descriptions (now includes objective)
        self._get_step_and_assert_description(workflow, "TASK_0", f"First Task in {objective}")
        self._get_step_and_assert_description(workflow, "TASK_1", f"Second Task in {objective}")

        # Check initial node statuses
        for node_id in ["START", "TASK_0", "TASK_1", "END"]:
            self._get_step_and_assert_status(workflow, node_id, ExecutionNodeStatus.NONE)

    def test_create_workflow_from_yaml(self):
        """Test creating a workflow from YAML data."""
        test_data = {
            "objective": "Test YAML workflow",
            "nodes": [
                {
                    "id": "TEST_NODE",
                    "type": "TASK",
                    "description": "Test node",
                    "objective": "Test objective"
                }
            ],
            "edges": [
                {
                    "source": "START",
                    "target": "TEST_NODE"
                },
                {
                    "source": "TEST_NODE",
                    "target": "END"
                }
            ],
            "prompts": {
                "task": "Custom task prompt"
            }
        }
        
        workflow = WorkflowFactory.from_yaml(test_data)
        
        assert isinstance(workflow, Workflow)
        assert workflow.objective is not None
        assert workflow.objective.current == "Test YAML workflow"
        assert "TEST_NODE" in workflow.nodes
        assert workflow.nodes["TEST_NODE"].objective is not None
        assert workflow.nodes["TEST_NODE"].objective.current == "Test objective"
        assert workflow.metadata.get("prompts", {}).get("task") == "Custom task prompt"

    def test_workflow_edge_handling(self):
        """Test workflow edge handling and validation."""
        objective = Objective("Test edge handling")
        workflow = WorkflowFactory.create_basic_workflow(
            objective,
            ["Task 1", "Task 2", "Task 3"]
        )

        # Test edge validation
        with self.assertRaises(ValueError):
            workflow.add_edge_between("NONEXISTENT", "START")

        with self.assertRaises(ValueError):
            workflow.add_edge_between("START", "NONEXISTENT")

        # Test edge retrieval
        start_edges = workflow.get_outgoing_edges("START")
        self.assertEqual(len(start_edges), 1)
        self.assertEqual(start_edges[0].target, "TASK_0")

    def _get_step_and_assert_type(self, workflow: Workflow, node_id: str, node_type: NodeType):
        """Helper method to assert node type."""
        node = workflow.get_step(node_id)
        assert node is not None
        self.assertEqual(node.node_type, node_type, f"{node_id} node type should be {node_type}")

    def _get_step_and_assert_description(self, workflow: Workflow, node_id: str, description: str):
        """Helper method to assert node description."""
        node = workflow.get_step(node_id)
        assert node is not None
        self.assertEqual(node.description, description, f"{node_id} node description should be {description}")

    def _get_step_and_assert_status(self, workflow: Workflow, node_id: str, status: ExecutionNodeStatus):
        """Helper method to assert node status."""
        node = workflow.get_step(node_id)
        assert node is not None
        self.assertEqual(node.status, status, f"{node_id} node status should be {status}")

if __name__ == '__main__':
    unittest.main()