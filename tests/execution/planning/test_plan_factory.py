"""Tests for PlanFactory."""

from opendxa import (
    PlanFactory,
    Plan,
    Objective,
    NodeType,
)

class TestPlanFactory:
    """Tests for PlanFactory."""

    def test_create_default_plan_from_config(self):
        """Test creating a plan from config."""
        objective = Objective("Test objective")
        plan = PlanFactory.create_from_config("default", objective)
        
        assert isinstance(plan, Plan)
        assert plan.objective == objective
        assert len(plan.nodes) >= 3  # At least START, one task, and END
        
        # Check that we have task nodes
        task_nodes = [node for node in plan.nodes.values()
                      if node.node_type == NodeType.TASK]
        assert len(task_nodes) > 0
        
        # Check that we have START and END nodes
        assert any(node.node_type == NodeType.START for node in plan.nodes.values())
        assert any(node.node_type == NodeType.END for node in plan.nodes.values())
        
        # Check that edges connect all nodes
        for node_id in plan.nodes:
            if node_id != "END":  # END should have no outgoing edges
                assert plan.get_outgoing_edges(node_id)
    
    def test_node_structure_and_metadata(self):
        """Test that nodes have correct structure and metadata."""
        objective = Objective("Test node structure")
        plan = PlanFactory.create_from_config("default", objective)
        
        # Check that we have the expected nodes from default config
        expected_nodes = ["START", "ANALYZE", "DESIGN", "IMPLEMENT", "VERIFY", "END"]
        for node_id in expected_nodes:
            assert node_id in plan.nodes, f"Missing expected node: {node_id}"
        
        # Check that task nodes have descriptions
        for node_id, node in plan.nodes.items():
            if node.node_type == NodeType.TASK:
                assert node.description, f"Node {node_id} has no description"
        
        # Check that nodes have metadata
        for node_id, node in plan.nodes.items():
            if node.node_type == NodeType.TASK:
                assert node.metadata is not None, f"Node {node_id} has no metadata"
                # Check for prompt in metadata
                assert "prompt" in node.metadata, f"Node {node_id} has no prompt in metadata"
    
    def test_edge_connections(self):
        """Test that edges properly connect all nodes."""
        objective = Objective("Test edge connections")
        plan = PlanFactory.create_from_config("default", objective)
        
        # Check that we have a linear sequence from START to END
        current = "START"
        visited = set()
        
        while current != "END":
            visited.add(current)
            outgoing = plan.get_outgoing_edges(current)
            assert len(outgoing) == 1, f"Node {current} should have exactly one outgoing edge"
            
            # Move to the next node
            current = outgoing[0].target
            
            # Prevent infinite loops
            assert current not in visited, f"Cycle detected at node {current}"
        
        # Check that we've visited all nodes
        all_nodes = set(plan.nodes.keys())
        assert visited.union({"END"}) == all_nodes, "Not all nodes were visited in the traversal"
    
    def test_role_setting(self):
        """Test that roles are properly set in metadata."""
        objective = Objective("Test role setting")
        role = "Test Planning Agent"
        plan = PlanFactory.create_from_config("default", objective, role=role)
        
        # Check that the role is set in metadata
        assert plan.metadata.get("role") == role, "Role not properly set in metadata"