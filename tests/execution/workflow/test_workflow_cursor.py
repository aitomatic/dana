"""Test workflow cursor functionality."""

from unittest.mock import Mock
import pytest

from dxa.common import NodeType
from dxa.execution import ExecutionContext, WorkflowFactory

@pytest.fixture
def mock_llm():  # pylint: disable=redefined-outer-name
    """Mock LLM for testing."""
    return Mock()

@pytest.fixture
def execution_context(mock_llm):  # pylint: disable=redefined-outer-name
    """Create execution context for testing."""
    return ExecutionContext(
        workflow_llm=mock_llm,
        planning_llm=mock_llm,
        reasoning_llm=mock_llm
    )

def test_workflow_cursor_update():
    """Test updating workflow cursor."""
    # Create a basic workflow
    workflow = WorkflowFactory.create_basic_workflow("Test workflow", ["Test task"])

    # Update cursor to START node
    workflow.update_cursor("START")
    node = workflow.get_current_node()
    assert node is not None
    assert node.node_id == "START"
    assert node.node_type == NodeType.START

def test_workflow_cursor_start():
    """Test workflow cursor initialization."""
    workflow = WorkflowFactory.create_basic_workflow("Test workflow", ["Test task"])
    cursor = workflow.start_cursor()

    # Cursor should start at START node
    assert cursor.current is not None
    assert cursor.current.node_id == "START"
    assert cursor.current.node_type == NodeType.START

def test_workflow_cursor_with_context(execution_context):  # pylint: disable=redefined-outer-name
    """Test workflow cursor with execution context."""
    workflow = WorkflowFactory.create_basic_workflow("Test workflow", ["Test task"])

    # Update cursor with context
    workflow.update_cursor("START")
    execution_context.current_workflow = workflow
    node = workflow.get_current_node()
    assert node is not None
    assert node.node_id == "START"
    assert node.node_type == NodeType.START

def test_workflow_cursor_invalid_node():
    """Test workflow cursor with invalid node."""
    workflow = WorkflowFactory.create_basic_workflow("Test workflow", ["Test task"])

    # Update to invalid node should raise ValueError
    with pytest.raises(ValueError):
        workflow.update_cursor("INVALID_NODE")

def test_workflow_cursor_empty_workflow():
    """Test workflow cursor with empty workflow."""
    workflow = WorkflowFactory.create_basic_workflow("Empty workflow", ["Empty task"])

    # Verify basic structure
    assert "START" in workflow.nodes
    assert "TASK_0" in workflow.nodes
    assert "END" in workflow.nodes

    # Verify node types
    assert workflow.nodes["START"].node_type == NodeType.START
    assert workflow.nodes["TASK_0"].node_type == NodeType.TASK
    assert workflow.nodes["END"].node_type == NodeType.END

    # Verify edges
    edges = workflow.get_outgoing_edges("START")
    assert len(edges) == 1
    assert edges[0].target == "TASK_0"

def test_workflow_cursor_edge_cases():
    """Test workflow cursor edge cases."""
    workflow = WorkflowFactory.create_basic_workflow("Test workflow", ["Test task"])

    # Test updating to current node
    workflow.update_cursor("START")
    workflow.update_cursor("START")  # Should not raise error
    node = workflow.get_current_node()
    assert node is not None
    assert node.node_id == "START"

    # Test updating to END node
    workflow.update_cursor("END")
    node = workflow.get_current_node()
    assert node is not None
    assert node.node_id == "END"
    assert node.node_type == NodeType.END
