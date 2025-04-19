"""Test workflow cursor functionality."""

from unittest.mock import Mock
import pytest

from opendxa import NodeType, ExecutionContext, PlanFactory

@pytest.fixture
def mock_llm():  # pylint: disable=redefined-outer-name
    """Mock LLM for testing."""
    return Mock()

@pytest.fixture
def execution_context(mock_llm):  # pylint: disable=redefined-outer-name
    """Create execution context for testing."""
    return ExecutionContext(
        planning_llm=mock_llm,
        reasoning_llm=mock_llm
    )

def test_plan_cursor_update():
    """Test updating plan cursor."""
    # Create a basic plan
    plan = PlanFactory.create_basic_plan("Test plan", ["Test task"])

    # Update cursor to START node
    plan.update_cursor("START")
    node = plan.get_current_node()
    assert node is not None
    assert node.node_id == "START"
    assert node.node_type == NodeType.START

def test_plan_cursor_start():
    """Test plan cursor initialization."""
    plan = PlanFactory.create_basic_plan("Test plan", ["Test task"])
    cursor = plan.start_cursor()

    # Cursor should start at START node
    assert cursor.current is not None
    assert cursor.current.node_id == "START"
    assert cursor.current.node_type == NodeType.START

def test_plan_cursor_with_context(execution_context):  # pylint: disable=redefined-outer-name
    """Test plan cursor with execution context."""
    plan = PlanFactory.create_basic_plan("Test plan", ["Test task"])

    # Update cursor with context
    plan.update_cursor("START")
    execution_context.current_plan = plan
    node = plan.get_current_node()
    assert node is not None
    assert node.node_id == "START"
    assert node.node_type == NodeType.START

def test_plan_cursor_invalid_node():
    """Test plan cursor with invalid node."""
    plan = PlanFactory.create_basic_plan("Test plan", ["Test task"])

    # Update to invalid node should raise ValueError
    with pytest.raises(ValueError):
        plan.update_cursor("INVALID_NODE")

def test_plan_cursor_empty_plan():
    """Test plan cursor with empty plan."""
    plan = PlanFactory.create_basic_plan("Empty plan", ["Empty task"])

    # Verify basic structure
    assert "START" in plan.nodes
    assert "TASK_0" in plan.nodes
    assert "END" in plan.nodes

    # Verify node types
    assert plan.nodes["START"].node_type == NodeType.START
    assert plan.nodes["TASK_0"].node_type == NodeType.TASK
    assert plan.nodes["END"].node_type == NodeType.END

    # Verify edges
    edges = plan.get_outgoing_edges("START")
    assert len(edges) == 1
    assert edges[0].target == "TASK_0"

def test_plan_cursor_edge_cases():
    """Test plan cursor edge cases."""
    plan = PlanFactory.create_basic_plan("Test plan", ["Test task"])

    # Test updating to current node
    plan.update_cursor("START")
    plan.update_cursor("START")  # Should not raise error
    node = plan.get_current_node()
    assert node is not None
    assert node.node_id == "START"

    # Test updating to END node
    plan.update_cursor("END")
    node = plan.get_current_node()
    assert node is not None
    assert node.node_id == "END"
    assert node.node_type == NodeType.END
