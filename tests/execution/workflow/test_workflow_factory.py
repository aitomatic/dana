"""Test workflow factory."""

import unittest
from pathlib import Path
from dxa.execution import WorkflowFactory
from dxa.execution import ExecutionNodeStatus
from dxa.common.graph import NodeType
from dxa.execution import Workflow
from dxa.execution import Objective

class TestWorkflowFactory(unittest.TestCase):
    """Test workflow factory."""

    def test_create_default_workflow(self):
        """Test default workflow."""
        workflow = WorkflowFactory.create_workflow_by_name("default", "Test Objective")
        self.assertEqual(len(workflow.nodes), 7)
        self.assertEqual(len(workflow.edges), 6)
        self._get_step_and_assert_description(workflow, "DEFINE", "Define the problem scope and objectives")

    def test_create_workflow_from_local_config(self):
        """Test creating a workflow from a local config directory."""
        # Path to the test config directory
        test_config_dir = Path(__file__).parent.parent.parent / "execution" / "workflow" / "config"
        
        # Verify the directory exists
        assert test_config_dir.exists(), f"Test config directory not found: {test_config_dir}"
        
        # Create a workflow using the local config
        objective = "Test local config"
        workflow = WorkflowFactory.create_from_config(
            "prosea_test",  # Assuming prosea_test.yaml exists in the test config dir
            objective,
            config_dir=test_config_dir
        )
        
        # Verify the workflow was created correctly
        assert isinstance(workflow, Workflow)
        assert workflow.objective is not None
        assert workflow.objective.original == objective
        
        # Check for specific nodes from the prosea_test config
        # These assertions will depend on what's in the prosea_test.yaml file
        assert "ANALYZE" in workflow.nodes, "ANALYZE node not found in workflow"
        
        # Test with a role
        role = "Local Config Test Agent"
        workflow_with_role = WorkflowFactory.create_from_config(
            "prosea_test",
            objective,
            role=role,
            config_dir=test_config_dir
        )
        
        # Verify the role was set
        assert workflow_with_role.metadata.get("role") == role 

    def test_create_sequential_workflow(self):
        """Test create_sequential_workflow."""
        # Define the objective and commands for the workflow
        objective = "Test Objective"
        commands = ["First Task", "Second Task"]

        # Create the workflow using the factory
        workflow = WorkflowFactory.create_basic_workflow(objective, commands)

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

    def test_create_minimal_workflow(self):
        """Test create_minimal_workflow with different inputs."""
        # Test with string objective
        workflow = WorkflowFactory.create_minimal_workflow("Test Objective")
        self.assertEqual(len(workflow.nodes), 3)
        self.assertEqual(len(workflow.edges), 2)
        self._get_step_and_assert_description(workflow, "PERFORM_TASK", "{objective}")

        # Test with Objective instance
        obj = Objective("Test Objective 2")
        workflow = WorkflowFactory.create_minimal_workflow(obj)
        self._get_step_and_assert_description(workflow, "PERFORM_TASK", "{objective}")

        # Test with None objective
        workflow = WorkflowFactory.create_minimal_workflow(None)
        self.assertEqual(len(workflow.nodes), 3)
        self._get_step_and_assert_description(workflow, "PERFORM_TASK", "{objective}")

        # Test node connections
        self.assertTrue(workflow.has_edge("START", "PERFORM_TASK"))
        self.assertTrue(workflow.has_edge("PERFORM_TASK", "END"))

        # Verify node types
        self._get_step_and_assert_type(workflow, "START", NodeType.START)
        self._get_step_and_assert_type(workflow, "PERFORM_TASK", NodeType.TASK)
        self._get_step_and_assert_type(workflow, "END", NodeType.END)

    def test_sequential_workflow_edge_cases(self):
        """Test create_sequential_workflow with edge cases."""
        # Test with empty commands list
        workflow = WorkflowFactory.create_basic_workflow("Empty Test", [])
        self.assertEqual(len(workflow.nodes), 2)  # Just START and END
        self.assertEqual(len(workflow.edges), 1)  # START -> END

        # Test with single command
        workflow = WorkflowFactory.create_basic_workflow("Single Test", ["Only Task"])
        self.assertEqual(len(workflow.nodes), 3)
        self._get_step_and_assert_description(workflow, "TASK_0", "Only Task")

        # Test with many commands
        many_commands = [f"Task {i}" for i in range(100)]
        workflow = WorkflowFactory.create_basic_workflow("Many Tests", many_commands)
        self.assertEqual(len(workflow.nodes), 102)  # 100 tasks + START + END
        self._get_step_and_assert_description(workflow, "TASK_99", "Task 99")

        # Test with Objective instance
        obj = Objective("Test with Objective")
        workflow = WorkflowFactory.create_basic_workflow(obj, ["Task 1", "Task 2"])
        self.assertEqual(workflow.objective, obj)

    def test_workflow_connectivity(self):
        """Test workflow graph connectivity."""
        workflow = WorkflowFactory.create_basic_workflow(
            "Test Connectivity", 
            ["Task 1", "Task 2", "Task 3"]
        )

        # Verify all nodes are reachable from START
        visited = set()

        def dfs(node_id):
            visited.add(node_id)
            for edge in workflow.edges:
                if edge.source == node_id and edge.target not in visited:
                    dfs(edge.target)

        dfs("START")
        self.assertEqual(len(visited), len(workflow.nodes))

        # Verify path exists from every node to END
        for node_id in workflow.nodes:
            if node_id != "END":
                path_exists = False
                current = node_id
                visited = set()
                while current in workflow.nodes:
                    if current == "END":
                        path_exists = True
                        break
                    visited.add(current)
                    # Find next node
                    for edge in workflow.edges:
                        if edge.source == current and edge.target not in visited:
                            current = edge.target
                            break
                    else:
                        break
                self.assertTrue(path_exists, f"No path from {node_id} to END")

    def test_node_id_generation(self):
        """Test node ID generation in sequential workflow."""
        workflow = WorkflowFactory.create_basic_workflow(
            "Test IDs", 
            ["First", "Second", "Third"]
        )

        # Verify task IDs are properly generated
        self.assertIn("TASK_0", workflow.nodes)
        self.assertIn("TASK_1", workflow.nodes)
        self.assertIn("TASK_2", workflow.nodes)

        # Verify descriptions match task IDs
        self._get_step_and_assert_description(workflow, "TASK_0", "First")
        self._get_step_and_assert_description(workflow, "TASK_1", "Second")
        self._get_step_and_assert_description(workflow, "TASK_2", "Third")

        # Verify START and END nodes exist
        self.assertIn("START", workflow.nodes)
        self.assertIn("END", workflow.nodes)

    def test_create_default_workflow_from_config(self):
        """Test creating a workflow from config."""
        objective = Objective("Test objective")
        workflow = WorkflowFactory.create_from_config("default", objective)
        
        assert isinstance(workflow, Workflow)
        assert workflow.objective == objective
        assert len(workflow.nodes) >= 3  # At least START, one task, and END
        
        # Check that we have task nodes
        task_nodes = [node for node in workflow.nodes.values()
                      if node.node_type == NodeType.TASK]
        assert len(task_nodes) > 0
        
        # Check that we have START and END nodes
        assert any(node.node_type == NodeType.START for node in workflow.nodes.values())
        assert any(node.node_type == NodeType.END for node in workflow.nodes.values())
        
        # Check that edges connect all nodes
        for node_id in workflow.nodes:
            if node_id != "END":  # END should have no outgoing edges
                assert workflow.get_outgoing_edges(node_id)
    
    def test_node_structure_and_metadata(self):
        """Test that nodes have correct structure and metadata."""
        objective = Objective("Test node structure")
        workflow = WorkflowFactory.create_from_config("default", objective)
        
        # Check that we have the expected nodes from default config
        expected_nodes = ["START", "DEFINE", "RESEARCH", "STRATEGIZE", "EXECUTE", "EVALUATE", "END"]
        for node_id in expected_nodes:
            assert node_id in workflow.nodes, f"Missing expected node: {node_id}"
        
        # Check that task nodes have descriptions
        for node_id, node in workflow.nodes.items():
            if node.node_type == NodeType.TASK:
                assert node.description, f"Node {node_id} has no description"
        
        # Check that nodes have metadata
        for node_id, node in workflow.nodes.items():
            if node.node_type == NodeType.TASK:
                assert node.metadata is not None, f"Node {node_id} has no metadata"
                # Check for prompt in metadata
                assert "prompt" in node.metadata, f"Node {node_id} has no prompt in metadata"
    
    def test_edge_connections(self):
        """Test that edges properly connect all nodes."""
        objective = Objective("Test edge connections")
        workflow = WorkflowFactory.create_from_config("default", objective)
        
        # Check that we have a linear sequence from START to END
        current = "START"
        visited = set()
        
        while current != "END":
            visited.add(current)
            outgoing = workflow.get_outgoing_edges(current)
            assert len(outgoing) == 1, f"Node {current} should have exactly one outgoing edge"
            
            # Move to the next node
            current = outgoing[0].target
            
            # Prevent infinite loops
            assert current not in visited, f"Cycle detected at node {current}"
        
        # Check that we've visited all nodes
        all_nodes = set(workflow.nodes.keys())
        assert visited.union({"END"}) == all_nodes, "Not all nodes were visited in the traversal"
    
    def test_role_setting(self):
        """Test that roles are properly set in metadata."""
        objective = Objective("Test role setting")
        role = "Test Workflow Agent"
        workflow = WorkflowFactory.create_from_config("default", objective, role=role)
        
        # Check that the role is set in metadata
        assert workflow.metadata.get("role") == role, "Role not properly set in metadata"
    
    def test_minimal_workflow(self):
        """Test creating a minimal workflow."""
        objective = "Test minimal workflow"
        workflow = WorkflowFactory.create_minimal_workflow(objective)
        
        assert isinstance(workflow, Workflow)
        assert workflow.objective is not None
        assert workflow.objective.original == objective
        
        # Check that we have exactly 3 nodes: START, PERFORM_TASK, END
        assert len(workflow.nodes) == 3
        assert "START" in workflow.nodes
        assert "PERFORM_TASK" in workflow.nodes
        assert "END" in workflow.nodes
        
        # Check that the task node has the objective as description
        # task_node = workflow.nodes["PERFORM_TASK"]
        # assert objective in task_node.description

if __name__ == '__main__':
    unittest.main()