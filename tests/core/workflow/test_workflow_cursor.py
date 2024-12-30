"""Test workflow cursor functionality."""

import pytest
from dxa.core.workflow import Workflow
from dxa.core.execution import Objective
from dxa.common.graph import NodeType

def test_workflow_cursor_update():
    """Test cursor updates in workflow."""
    workflow = Workflow(objective=Objective("test"))
    
    # Should have START -> TASK -> END structure
    assert "START" in workflow.nodes
    assert "ANSWER_QUESTION" in workflow.nodes
    
    # Test cursor movement
    workflow.update_cursor("START")
    assert workflow.get_current_node().node_type == NodeType.START
    
    workflow.update_cursor("ANSWER_QUESTION")
    assert workflow.get_current_node().node_type == NodeType.TASK

def test_workflow_cursor_validation():
    """Test cursor validation."""
    workflow = Workflow(objective=Objective("test"))
    
    with pytest.raises(ValueError):
        workflow.update_cursor("INVALID_NODE") 

def test_workflow_cursor_start():
    """Test cursor initialization at START node."""
    workflow = Workflow(objective=Objective("test"))
    cursor = workflow.start_cursor()
    assert cursor.current.node_type == NodeType.START 