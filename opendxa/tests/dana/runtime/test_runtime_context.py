"""Tests for the DANA runtime context."""

import pytest

from opendxa.dana.exceptions import StateError
from opendxa.dana.runtime.context import ExecutionStatus, RuntimeContext


def test_runtime_context_scopes():
    """Test scope-based access in RuntimeContext."""
    ctx = RuntimeContext()

    # Test agent scope
    ctx.set("agent.name", "Alice")
    assert ctx.get("agent.name") == "Alice"

    # Test world scope
    ctx.set("world.temperature", 25)
    assert ctx.get("world.temperature") == 25

    # Test shared scope
    ctx.set("shared.counter", 0)
    assert ctx.get("shared.counter") == 0

    # Test invalid scope
    with pytest.raises(StateError):
        ctx.set("invalid.key", "value")

    with pytest.raises(StateError):
        ctx.get("invalid.key")


def test_runtime_context_nested_keys():
    """Test nested key access in RuntimeContext."""
    ctx = RuntimeContext()

    # Test nested keys in agent scope
    ctx.set("agent.profile.name", "Alice")
    ctx.set("agent.profile.age", 30)
    assert ctx.get("agent.profile.name") == "Alice"
    assert ctx.get("agent.profile.age") == 30

    # Test nested keys in world scope
    ctx.set("world.sensor.temperature", 25)
    ctx.set("world.sensor.status", "active")
    assert ctx.get("world.sensor.temperature") == 25
    assert ctx.get("world.sensor.status") == "active"

    # Test nested keys in shared scope
    ctx.set("shared.config.debug", True)
    ctx.set("shared.config.log_level", "info")
    assert ctx.get("shared.config.debug") is True
    assert ctx.get("shared.config.log_level") == "info"


def test_execution_state():
    """Test execution state management."""
    ctx = RuntimeContext()

    # Test initial state
    assert ctx.get_execution_status() == ExecutionStatus.IDLE
    assert ctx.get("shared.execution.current_node_id") is None
    assert ctx.get("shared.execution.node_results") == {}
    assert ctx.get("shared.execution.history") == []
    assert ctx.get("shared.execution.visited_nodes") == []
    assert ctx.get("shared.execution.execution_path") == []

    # Test updating execution state
    ctx.set_execution_status(ExecutionStatus.RUNNING)
    assert ctx.get_execution_status() == ExecutionStatus.RUNNING

    ctx.update_execution_node("node1", "result1")
    assert ctx.get("shared.execution.current_node_id") == "node1"
    assert ctx.get("shared.execution.node_results") == {"node1": "result1"}
    assert ctx.get("shared.execution.visited_nodes") == ["node1"]

    ctx.update_execution_node("node2", "result2")
    assert ctx.get("shared.execution.current_node_id") == "node2"
    assert ctx.get("shared.execution.node_results") == {"node1": "result1", "node2": "result2"}
    assert ctx.get("shared.execution.visited_nodes") == ["node1", "node2"]
    assert ctx.get("shared.execution.execution_path") == [("node1", "node2")]

    # Test execution history
    ctx.add_execution_history({"action": "started"})
    history = ctx.get("shared.execution.history")
    assert len(history) == 1
    assert "action" in history[0]
    assert "timestamp" in history[0]

    # Test reset
    ctx.reset_execution_state()
    assert ctx.get_execution_status() == ExecutionStatus.IDLE
    assert ctx.get("shared.execution.current_node_id") is None
    assert ctx.get("shared.execution.node_results") == {}
    assert ctx.get("shared.execution.history") == []
    assert ctx.get("shared.execution.visited_nodes") == []
    assert ctx.get("shared.execution.execution_path") == []


def test_resource_management():
    """Test resource management functionality."""
    ctx = RuntimeContext()

    # Register a resource
    ctx.register_resource("llm", "mock_llm")
    assert ctx.get_resource("llm") == "mock_llm"
    assert "llm" in ctx.list_resources()

    # Test getting non-existent resource
    with pytest.raises(StateError):
        ctx.get_resource("nonexistent")

    # Test registering empty name
    with pytest.raises(StateError):
        ctx.register_resource("", "value")


def test_invalid_keys():
    """Test handling of invalid keys."""
    ctx = RuntimeContext()

    # Test un-scoped keys
    with pytest.raises(StateError):
        ctx.get("unscoped_key")

    with pytest.raises(StateError):
        ctx.set("unscoped_key", "value")

    # Test empty keys
    with pytest.raises(StateError):
        ctx.get(".")

    with pytest.raises(StateError):
        ctx.set(".", "value")

    # Test invalid scope
    with pytest.raises(StateError):
        ctx.get("invalid.key")

    with pytest.raises(StateError):
        ctx.set("invalid.key", "value")
