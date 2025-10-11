import pytest

from dana_lang.api.core.schemas_v2 import DomainKnowledgeTreeV2, DomainNodeV2


class TestDomainKnowledgeTreeV2:
    """Test cases for DomainKnowledgeTreeV2.delete_node method"""

    def test_delete_root_node(self):
        """Test deleting the root node itself"""
        child1 = DomainNodeV2(topic="child1", children=[])
        root = DomainNodeV2(topic="root", children=[child1])
        tree = DomainKnowledgeTreeV2(root=root)

        # Delete root node
        with pytest.raises(ValueError, match="Cannot delete root node"):
            tree.delete_node("root")

    def test_delete_child_of_root(self):
        """Test deleting a child of the root node"""
        child1 = DomainNodeV2(topic="child1", children=[])
        child2 = DomainNodeV2(topic="child2", children=[])
        root = DomainNodeV2(topic="root", children=[child1, child2])
        tree = DomainKnowledgeTreeV2(root=root)

        # Delete child1
        tree.delete_node("root/child1")

        # Verify child1 is deleted
        assert len(tree.root.children) == 1
        assert tree.root.children[0].topic == "child2"

    def test_delete_nested_node(self):
        """Test deleting a deeply nested node"""
        # Create: root -> child1 -> grandchild1 -> greatgrandchild1
        greatgrandchild1 = DomainNodeV2(topic="greatgrandchild1", children=[])
        grandchild1 = DomainNodeV2(topic="grandchild1", children=[greatgrandchild1])
        child1 = DomainNodeV2(topic="child1", children=[grandchild1])
        root = DomainNodeV2(topic="root", children=[child1])
        tree = DomainKnowledgeTreeV2(root=root)

        # Delete greatgrandchild1
        tree.delete_node("root/child1/grandchild1/greatgrandchild1")

        # Verify greatgrandchild1 is deleted
        assert len(tree.root.children[0].children[0].children) == 0

    def test_delete_node_wrong_root(self):
        """Test deleting with wrong root node name"""
        child1 = DomainNodeV2(topic="child1", children=[])
        root = DomainNodeV2(topic="root", children=[child1])
        tree = DomainKnowledgeTreeV2(root=root)

        # Try to delete with wrong root name
        with pytest.raises(ValueError, match="Root node 'root' doesn't match path 'wrongroot'"):
            tree.delete_node("wrongroot/child1")

    def test_delete_node_with_list_path(self):
        """Test deleting using list path"""
        child1 = DomainNodeV2(topic="child1", children=[])
        root = DomainNodeV2(topic="root", children=[child1])
        tree = DomainKnowledgeTreeV2(root=root)

        # Delete using list path
        tree.delete_node(["root", "child1"])

        # Verify child1 is deleted
        assert len(tree.root.children) == 0

    def test_delete_node_with_empty_path(self):
        """Test deleting with empty path"""
        child1 = DomainNodeV2(topic="child1", children=[])
        root = DomainNodeV2(topic="root", children=[child1])
        tree = DomainKnowledgeTreeV2(root=root)

        # Delete with empty path - should not modify anything
        tree.delete_node([])
        assert len(tree.root.children) == 1

    def test_delete_node_with_empty_string_path(self):
        """Test deleting with empty string path"""
        child1 = DomainNodeV2(topic="child1", children=[])
        root = DomainNodeV2(topic="root", children=[child1])
        tree = DomainKnowledgeTreeV2(root=root)

        # Delete with empty string path - should not modify anything
        tree.delete_node("")
        assert len(tree.root.children) == 1

    def test_delete_node_complex_tree(self):
        """Test deleting nodes in a complex tree structure"""
        # Create a complex tree:
        # root -> child1 -> grandchild1, grandchild2
        #       -> child2 -> grandchild3
        #       -> child3 -> grandchild4 -> greatgrandchild1
        greatgrandchild1 = DomainNodeV2(topic="greatgrandchild1", children=[])
        grandchild1 = DomainNodeV2(topic="grandchild1", children=[])
        grandchild2 = DomainNodeV2(topic="grandchild2", children=[])
        grandchild3 = DomainNodeV2(topic="grandchild3", children=[])
        grandchild4 = DomainNodeV2(topic="grandchild4", children=[greatgrandchild1])

        child1 = DomainNodeV2(topic="child1", children=[grandchild1, grandchild2])
        child2 = DomainNodeV2(topic="child2", children=[grandchild3])
        child3 = DomainNodeV2(topic="child3", children=[grandchild4])

        root = DomainNodeV2(topic="root", children=[child1, child2, child3])
        tree = DomainKnowledgeTreeV2(root=root)

        # Delete child2 (which has grandchild3)
        tree.delete_node("root/child2")

        # Verify child2 is deleted
        assert len(tree.root.children) == 2
        assert tree.root.children[0].topic == "child1"
        assert tree.root.children[1].topic == "child3"

        # Delete grandchild4 (which has greatgrandchild1)
        tree.delete_node("root/child3/grandchild4")

        # Verify grandchild4 and greatgrandchild1 are deleted
        assert len(tree.root.children[1].children) == 0


class TestIntegrationScenarios:
    """Integration tests for both DomainNodeV2 and DomainKnowledgeTreeV2"""

    def test_create_and_delete_complete_workflow(self):
        """Test a complete workflow of creating and deleting nodes"""
        # Create a tree structure
        leaf1 = DomainNodeV2(topic="leaf1", children=[])
        leaf2 = DomainNodeV2(topic="leaf2", children=[])
        leaf3 = DomainNodeV2(topic="leaf3", children=[])

        branch1 = DomainNodeV2(topic="branch1", children=[leaf1, leaf2])
        branch2 = DomainNodeV2(topic="branch2", children=[leaf3])

        root = DomainNodeV2(topic="root", children=[branch1, branch2])
        tree = DomainKnowledgeTreeV2(root=root)

        # Verify initial structure
        assert len(tree.root.children) == 2
        assert len(tree.root.children[0].children) == 2
        assert len(tree.root.children[1].children) == 1

        # Delete leaf1 from branch1
        tree.delete_node("root/branch1/leaf1")
        assert len(tree.root.children[0].children) == 1
        assert tree.root.children[0].children[0].topic == "leaf2"

        # Delete entire branch2
        tree.delete_node("root/branch2")
        assert len(tree.root.children) == 1
        assert tree.root.children[0].topic == "branch1"

        # Delete remaining leaf from branch1
        tree.delete_node("root/branch1/leaf2")
        assert len(tree.root.children[0].children) == 0

    def test_error_handling_consistency(self):
        """Test that error handling is consistent between both classes"""
        # Test DomainKnowledgeTreeV2 error handling
        root = DomainNodeV2(topic="root", children=[])
        tree = DomainKnowledgeTreeV2(root=root)
        with pytest.raises(ValueError, match="Root node 'root' doesn't match path 'wrong'"):
            tree.delete_node("wrong/child")

    def test_path_format_consistency(self):
        """Test that both classes handle path formats consistently"""
        # Create test structure
        child = DomainNodeV2(topic="child", children=[])
        root = DomainNodeV2(topic="root", children=[child])
        tree = DomainKnowledgeTreeV2(root=root)

        # Test string path
        tree.delete_node("root/child")
        assert len(tree.root.children) == 0

        # Recreate structure
        child = DomainNodeV2(topic="child", children=[])
        root = DomainNodeV2(topic="root", children=[child])
        tree = DomainKnowledgeTreeV2(root=root)

        # Test list path
        tree.delete_node(["root", "child"])
        assert len(tree.root.children) == 0


if __name__ == "__main__":
    pytest.main([__file__])
