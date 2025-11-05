"""
Unit tests for ModifyTreeTool to ensure node status is preserved during operations.

Tests verify that:
1. Node status is preserved when creating new nodes (existing nodes keep their status)
2. Node status is preserved when modifying nodes (renaming doesn't remove status)
3. Node status is preserved when removing nodes (other nodes keep their status)
"""

import pytest
from datetime import datetime, UTC

from dana.studio.api.services.intent_detection.intent_handlers.handler_tools.knowledge_ops_tools.modify_tree_tool import (
    ModifyTreeTool,
)
from dana.studio.api.core.schemas_v2 import (
    DomainKnowledgeTreeV2 as DomainKnowledgeTree,
    DomainNodeV2 as DomainNode,
    KnowledgeGenerationStatus,
)


class TestModifyTreeToolNodeStatusPreservation:
    """Test that node status is preserved during tree operations."""

    @pytest.fixture
    def tree_with_statuses(self):
        """Create a tree with nodes that have different statuses."""
        root = DomainNode(
            topic="Financial Analysis",
            status=KnowledgeGenerationStatus.COMPLETED,
            children=[
                DomainNode(
                    topic="Risk Analysis",
                    status=KnowledgeGenerationStatus.GENERATING,
                    children=[
                        DomainNode(topic="Market Risk", status=KnowledgeGenerationStatus.PENDING),
                        DomainNode(topic="Credit Risk", status=KnowledgeGenerationStatus.QUESTION_GENERATED),
                    ],
                ),
                DomainNode(
                    topic="Performance Metrics",
                    status=KnowledgeGenerationStatus.COMPLETED,
                    children=[
                        DomainNode(topic="ROI", status=KnowledgeGenerationStatus.COMPLETED),
                    ],
                ),
            ],
        )
        tree = DomainKnowledgeTree(root=root, last_updated=datetime.now(UTC), version=1)
        return tree

    @pytest.fixture
    def modify_tool(self, tree_with_statuses, tmp_path):
        """Create ModifyTreeTool instance with test tree."""
        domain_knowledge_path = tmp_path / "domain_knowledge.json"
        storage_path = tmp_path / "storage"
        storage_path.mkdir()

        tool = ModifyTreeTool(
            tree_structure=tree_with_statuses,
            domain_knowledge_path=str(domain_knowledge_path),
            storage_path=str(storage_path),
            domain="Finance",
            role="Financial Analyst",
        )
        return tool

    def test_create_node_preserves_existing_node_statuses(self, modify_tool):
        """Test that creating new nodes preserves status of existing nodes."""
        # Store original statuses
        original_root_status = modify_tool.tree_structure.root.status
        original_risk_status = modify_tool.tree_structure.root.children[0].status
        original_market_risk_status = modify_tool.tree_structure.root.children[0].children[0].status

        # Create a new node under Risk Analysis
        result = modify_tool._create_single_node(
            ["Financial Analysis", "Risk Analysis", "Operational Risk"], "Financial Analysis > Risk Analysis > Operational Risk"
        )

        # Verify operation succeeded
        assert result["success"] is True
        assert result["total_created"] == 1

        # Verify existing node statuses are preserved
        assert modify_tool.tree_structure.root.status == original_root_status
        assert modify_tool.tree_structure.root.children[0].status == original_risk_status
        assert modify_tool.tree_structure.root.children[0].children[0].status == original_market_risk_status

        # Verify new node has default PENDING status
        new_node = None
        for child in modify_tool.tree_structure.root.children[0].children:
            if child.topic == "Operational Risk":
                new_node = child
                break

        assert new_node is not None
        assert new_node.status == KnowledgeGenerationStatus.PENDING

    def test_create_node_preserves_all_existing_statuses(self, modify_tool):
        """Test that creating nodes at different levels preserves all existing statuses."""
        # Store all original statuses
        original_statuses = {}

        def collect_statuses(node, path=""):
            current_path = f"{path}/{node.topic}" if path else node.topic
            original_statuses[current_path] = node.status
            for child in node.children:
                collect_statuses(child, current_path)

        collect_statuses(modify_tool.tree_structure.root)

        # Create a new branch
        result = modify_tool._create_single_node(
            ["Financial Analysis", "Compliance", "Regulatory Requirements"], "Financial Analysis > Compliance > Regulatory Requirements"
        )

        assert result["success"] is True

        # Verify all original statuses are preserved
        def verify_statuses(node, path=""):
            current_path = f"{path}/{node.topic}" if path else node.topic
            if current_path in original_statuses:
                assert node.status == original_statuses[current_path], f"Status changed for node at path {current_path}"
            for child in node.children:
                verify_statuses(child, current_path)

        verify_statuses(modify_tool.tree_structure.root)

    def test_modify_node_preserves_status(self, modify_tool):
        """Test that modifying a node (renaming) preserves its status."""
        # Get the node to modify
        target_node = modify_tool.tree_structure.root.children[0]  # Risk Analysis
        original_status = target_node.status
        original_children_statuses = {}
        for child in target_node.children:
            original_children_statuses[child.topic] = child.status

        # Modify the node (rename)
        result = modify_tool._modify_single_node(
            ["Financial Analysis", "Risk Analysis"], "Financial Analysis > Risk Analysis", new_name="Risk Assessment"
        )

        # Verify operation succeeded
        assert result["success"] is True
        assert result["renamed"] is True

        # Verify the node's status is preserved
        modified_node = modify_tool.tree_structure.root.children[0]
        assert modified_node.status == original_status, "Node status should be preserved after rename"
        assert modified_node.topic == "Risk Assessment", "Node name should be updated"

        # Verify children statuses are preserved
        for child in modified_node.children:
            assert child.status == original_children_statuses[child.topic], f"Child status should be preserved for {child.topic}"

    def test_modify_node_without_rename_preserves_status(self, modify_tool):
        """Test that modifying a node without renaming still preserves status."""
        target_node = modify_tool.tree_structure.root.children[1]  # Performance Metrics
        original_status = target_node.status

        # Modify without renaming (just metadata update)
        result = modify_tool._modify_single_node(
            ["Financial Analysis", "Performance Metrics"], "Financial Analysis > Performance Metrics", new_name=None
        )

        assert result["success"] is True
        assert result["renamed"] is False

        # Verify status is preserved
        assert target_node.status == original_status

    def test_remove_node_preserves_other_nodes_status(self, modify_tool):
        """Test that removing a node preserves status of remaining nodes."""
        # Store statuses of nodes that should remain
        root_status = modify_tool.tree_structure.root.status
        performance_metrics_status = modify_tool.tree_structure.root.children[1].status
        roi_status = modify_tool.tree_structure.root.children[1].children[0].status

        # Remove Risk Analysis node
        result = modify_tool._remove_single_node(["Financial Analysis", "Risk Analysis"], "Financial Analysis > Risk Analysis")

        assert result["success"] is True

        # Verify remaining nodes keep their statuses
        assert modify_tool.tree_structure.root.status == root_status
        assert len(modify_tool.tree_structure.root.children) == 1
        remaining_node = modify_tool.tree_structure.root.children[0]
        assert remaining_node.status == performance_metrics_status
        assert remaining_node.children[0].status == roi_status

    def test_bulk_operations_preserve_all_statuses(self, modify_tool):
        """Test that bulk operations preserve node statuses across all operations."""
        # Store all original statuses
        original_statuses = {}

        def collect_statuses(node, path=""):
            current_path = f"{path}/{node.topic}" if path else node.topic
            original_statuses[current_path] = node.status
            for child in node.children:
                collect_statuses(child, current_path)

        collect_statuses(modify_tool.tree_structure.root)

        # Perform bulk operations
        bulk_ops = [
            {"action": "create", "paths": ["Financial Analysis", "Compliance", "Audit"]},
            {"action": "modify", "paths": ["Financial Analysis", "Performance Metrics"], "new_name": "Performance Analysis"},
        ]

        result = modify_tool._execute_bulk_operations(bulk_ops)

        # Verify operations succeeded (check for success indicators)
        assert "Successfully completed" in result or "Operations Performed" in result

        # Verify all original statuses are preserved
        def verify_statuses(node, path=""):
            current_path = f"{path}/{node.topic}" if path else node.topic
            if current_path in original_statuses:
                assert node.status == original_statuses[current_path], f"Status changed for node at path {current_path}"
            for child in node.children:
                verify_statuses(child, current_path)

        verify_statuses(modify_tool.tree_structure.root)

    def test_create_node_defaults_to_pending_status(self, modify_tool):
        """Test that newly created nodes default to PENDING status."""
        # Create a new node
        result = modify_tool._create_single_node(
            ["Financial Analysis", "New Category", "New Topic"], "Financial Analysis > New Category > New Topic"
        )

        assert result["success"] is True

        # Find the newly created nodes
        new_category = None
        for child in modify_tool.tree_structure.root.children:
            if child.topic == "New Category":
                new_category = child
                break

        assert new_category is not None
        assert new_category.status == KnowledgeGenerationStatus.PENDING

        new_topic = None
        for child in new_category.children:
            if child.topic == "New Topic":
                new_topic = child
                break

        assert new_topic is not None
        assert new_topic.status == KnowledgeGenerationStatus.PENDING

    def test_modify_root_node_preserves_status(self, modify_tool):
        """Test that modifying root node preserves its status."""
        original_status = modify_tool.tree_structure.root.status

        # Modify root (without renaming for now, as root rename is restricted)
        result = modify_tool._modify_single_node(["Financial Analysis"], "Financial Analysis", new_name=None)

        assert result["success"] is True

        # Verify root status is preserved
        assert modify_tool.tree_structure.root.status == original_status

    def test_nested_node_status_preservation(self, modify_tool):
        """Test that deeply nested node statuses are preserved."""
        # Get a deeply nested node
        market_risk_node = modify_tool.tree_structure.root.children[0].children[0]
        original_status = market_risk_node.status

        # Create a sibling node
        result = modify_tool._create_single_node(
            ["Financial Analysis", "Risk Analysis", "Liquidity Risk"], "Financial Analysis > Risk Analysis > Liquidity Risk"
        )

        assert result["success"] is True

        # Verify the original nested node status is preserved
        market_risk_node = modify_tool.tree_structure.root.children[0].children[0]
        assert market_risk_node.status == original_status
