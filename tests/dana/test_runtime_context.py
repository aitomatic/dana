"""Tests for the DANA runtime context."""

import pytest

from opendxa.dana.exceptions import StateError
from opendxa.dana.runtime.context import ExecutionStatus, RuntimeContext


def test_runtime_context_scopes():
    """Test scope-based access in RuntimeContext."""
    ctx = RuntimeContext()

    # Test private scope
    ctx.set("private.name", "Alice")
    assert ctx.get("private.name") == "Alice"

    # Test group scope
    ctx.set("group.temperature", 25)
    assert ctx.get("group.temperature") == 25

    # Test global scope
    ctx.set("global.weather", "sunny")
    assert ctx.get("global.weather") == "sunny"

    # Test execution scope
    ctx.set("execution.status", "running")
    assert ctx.get("execution.status") == "running"


def test_runtime_context_nested_keys():
    """Test nested key access in RuntimeContext."""
    ctx = RuntimeContext()

    # Test nested keys in private scope
    ctx.set("private.profile.name", "Alice")
    ctx.set("private.profile.age", 30)
    assert ctx.get("private.profile.name") == "Alice"
    assert ctx.get("private.profile.age") == 30

    # Test nested keys in group scope
    ctx.set("group.settings.theme", "dark")
    assert ctx.get("group.settings.theme") == "dark"

    # Test nested keys in global scope
    ctx.set("global.location.city", "San Francisco")
    assert ctx.get("global.location.city") == "San Francisco"

    # Test nested keys in execution scope
    ctx.set("execution.history.last_action", "completed")
    assert ctx.get("execution.history.last_action") == "completed"


def test_execution_state():
    """Test execution state management."""
    ctx = RuntimeContext()

    # Test initial state
    assert ctx.get_execution_status() == ExecutionStatus.IDLE
    assert ctx.get("execution.current_node_id") is None

    # Test updating execution state
    ctx.update_execution_node("node1", "result1")
    assert ctx.get("execution.current_node_id") == "node1"
    assert ctx.get("execution.node_results")["node1"] == "result1"

    # Test execution path
    ctx.update_execution_node("node2", "result2")
    execution_path = ctx.get("execution.execution_path")
    assert len(execution_path) == 1
    assert execution_path[0] == ("node1", "node2")

    # Test visited nodes
    visited_nodes = ctx.get("execution.visited_nodes")
    assert len(visited_nodes) == 2
    assert visited_nodes == ["node1", "node2"]

    # Test execution history
    ctx.add_execution_history({"action": "test"})
    history = ctx.get("execution.history")
    assert len(history) == 1
    assert history[0]["action"] == "test"
    assert "timestamp" in history[0]

    # Test status update
    ctx.set_execution_status(ExecutionStatus.RUNNING)
    assert ctx.get_execution_status() == ExecutionStatus.RUNNING

    # Test reset
    ctx.reset_execution_state()
    assert ctx.get_execution_status() == ExecutionStatus.IDLE
    assert ctx.get("execution.current_node_id") is None
    assert not ctx.get("execution.node_results")
    assert not ctx.get("execution.history")
    assert not ctx.get("execution.visited_nodes")
    assert not ctx.get("execution.execution_path")


def test_resource_management():
    """Test resource management functionality."""
    ctx = RuntimeContext()

    # Test registering and retrieving resources
    resource = {"type": "test", "value": 42}
    ctx.register_resource("test_resource", resource)
    assert ctx.get_resource("test_resource") == resource

    # Test listing resources
    assert "test_resource" in ctx.list_resources()

    # Test getting nonexistent resource
    with pytest.raises(StateError):
        ctx.get_resource("nonexistent")


def test_invalid_keys():
    """Test handling of invalid state keys."""
    ctx = RuntimeContext()

    # Test invalid scope
    with pytest.raises(StateError) as exc_info:
        ctx.set("invalid.key", "value")
    assert "Unknown scope" in str(exc_info.value)

    # Test empty variable name
    with pytest.raises(StateError) as exc_info:
        ctx.set("private.", "value")
    assert "Invalid state key" in str(exc_info.value)

    # Test missing scope
    with pytest.raises(StateError) as exc_info:
        ctx.set(".value", "test")
    assert "Invalid state key" in str(exc_info.value)

    # Test missing variable
    with pytest.raises(StateError) as exc_info:
        ctx.set("private", "test")
    assert "Invalid state key" in str(exc_info.value)
