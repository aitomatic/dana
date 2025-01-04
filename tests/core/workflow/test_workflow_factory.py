import unittest
from dxa.core.workflow.workflow_factory import WorkflowFactory
from dxa.core.execution.execution_graph import ExecutionNodeStatus
from dxa.common.graph.directed_graph import NodeType

class TestWorkflowFactory(unittest.TestCase):
    def test_create_sequential_workflow(self):
        # Define the objective and commands for the workflow
        objective = "Test Objective"
        commands = ["First Task", "Second Task"]

        # Create the workflow using the factory
        workflow = WorkflowFactory.create_sequential_workflow(objective, commands)

        # Assertions
        self.assertEqual(len(workflow.nodes), 4, "Workflow should have 4 nodes (including START and END)")
        self.assertEqual(len(workflow.edges), 3, "Workflow should have 3 edges")

        # Check node types and descriptions
        self.assertEqual(workflow.get_step("START").node_type, NodeType.START, "Start node type should be START")
        self.assertEqual(workflow.get_step("TASK_0").node_type, NodeType.TASK, "First task node type should be TASK")
        self.assertEqual(workflow.get_step("TASK_1").node_type, NodeType.TASK, "Second task node type should be TASK")
        self.assertEqual(workflow.get_step("END").node_type, NodeType.END, "End node type should be END")

        # Check node descriptions
        self.assertEqual(workflow.get_step("TASK_0").description, "First Task", "First task description should match")
        self.assertEqual(workflow.get_step("TASK_1").description, "Second Task", "Second task description should match")

        # Check initial node statuses
        for node_id in ["START", "TASK_0", "TASK_1", "END"]:
            self.assertEqual(workflow.get_step(node_id).status, ExecutionNodeStatus.PENDING, f"{node_id} node status should be PENDING")

if __name__ == '__main__':
    unittest.main()
