"""Test workflow cursor functionality."""

import pytest
from dxa.execution import WorkflowFactory
from dxa.common.graph import NodeType

def test_workflow_cursor_update():
    """Test cursor updates in workflow."""
    workflow = WorkflowFactory.create_minimal_workflow("test")
    
    # Should have START -> TASK -> END structure
    assert "START" in workflow.nodes
    assert "PERFORM_TASK" in workflow.nodes
    
    # Test cursor movement
    workflow.update_cursor("START")
    node = workflow.get_current_node()
    assert node is not None
    assert node.node_type == NodeType.START
    
    workflow.update_cursor("PERFORM_TASK")
    node = workflow.get_current_node()
    assert node is not None
    assert node.node_type == NodeType.TASK

def test_workflow_cursor_validation():
    """Test cursor validation."""
    workflow = WorkflowFactory.create_minimal_workflow("test")
    
    with pytest.raises(ValueError):
        workflow.update_cursor("INVALID_NODE") 

def test_workflow_cursor_start():
    """Test cursor initialization at START node."""
    workflow = WorkflowFactory.create_minimal_workflow("test")
    cursor = workflow.start_cursor()
    assert cursor.current.node_type == NodeType.START 
