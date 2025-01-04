"""Test workflow factory."""

import unittest
from dxa.core.workflow.workflow_factory import WorkflowFactory
from dxa.core.execution.execution_graph import ExecutionNodeStatus
from dxa.common.graph.directed_graph import NodeType
from dxa.core.workflow.workflow import Workflow

class TestWorkflowFactory(unittest.TestCase):
    """Test workflow factory."""

    def test_create_sequential_workflow(self):
        """Test create_sequential_workflow."""
        # Define the objective and commands for the workflow
        objective = "Test Objective"
        commands = ["First Task", "Second Task"]

        # Create the workflow using the factory
        workflow = WorkflowFactory.create_sequential_workflow(objective, commands)

        # Assertions
        self.assertEqual(len(workflow.nodes), 4, "Workflow should have 4 nodes (including START and END)")
        self.assertEqual(len(workflow.edges), 3, "Workflow should have 3 edges")

        # Check node types and descriptions
        self._get_step_and_assert_type(workflow, "START", NodeType.START)
        self._get_step_and_assert_type(workflow, "TASK_0", NodeType.TASK)
        self._get_step_and_assert_type(workflow, "TASK_1", NodeType.TASK)
        self._get_step_and_assert_type(workflow, "END", NodeType.END)

        # Check node descriptions
        self._get_step_and_assert_description(workflow, "TASK_0", "First Task")
        self._get_step_and_assert_description(workflow, "TASK_1", "Second Task")

        # Check initial node statuses
        for node_id in ["START", "TASK_0", "TASK_1", "END"]:
            self._get_step_and_assert_status(workflow, node_id, ExecutionNodeStatus.NONE)
    
    def _get_step_and_assert_type(self, workflow: Workflow, node_id: str, node_type: NodeType):
        node = workflow.get_step(node_id)
        assert node is not None
        self.assertEqual(node.node_type, node_type, f"{node_id} node type should be {node_type}")

    def _get_step_and_assert_description(self, workflow: Workflow, node_id: str, description: str):
        node = workflow.get_step(node_id)
        assert node is not None
        self.assertEqual(node.description, description, f"{node_id} node description should be {description}")

    def _get_step_and_assert_status(self, workflow: Workflow, node_id: str, status: ExecutionNodeStatus):
        node = workflow.get_step(node_id)
        assert node is not None
        self.assertEqual(node.status, status, f"{node_id} node status should be {status}")

if __name__ == '__main__':
    unittest.main()