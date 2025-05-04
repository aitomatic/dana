"""Tests for the DANA runtime context."""

import pytest

from opendxa.dana.exceptions import RuntimeError
from opendxa.dana.runtime.runtime_context import RuntimeContext, StateContainer


def test_state_container_nested_access():
    """Test nested key access in StateContainer."""
    state = StateContainer({"user": {"profile": {"name": "Alice", "age": 30}, "preferences": {"theme": "dark"}}})

    # Test getting nested values
    assert state.get("user.profile.name") == "Alice"
    assert state.get("user.profile.age") == 30
    assert state.get("user.preferences.theme") == "dark"
    assert state.get("user.profile.nonexistent") is None
    assert state.get("nonexistent.key", "default") == "default"

    # Test setting nested values
    state.set("user.profile.name", "Bob")
    assert state.get("user.profile.name") == "Bob"

    # Test creating new nested paths
    state.set("user.settings.notifications.enabled", True)
    assert state.get("user.settings.notifications.enabled") is True


def test_runtime_context_scopes():
    """Test scope-based access in RuntimeContext."""
    ctx = RuntimeContext()

    # Test agent scope
    ctx.set("agent:name", "Alice")
    assert ctx.get("agent:name") == "Alice"

    # Test world scope
    ctx.set("world:temperature", 25)
    assert ctx.get("world:temperature") == 25

    # Test execution scope
    ctx.set("execution:status", "running")
    assert ctx.get("execution:status") == "running"

    # Test invalid scope
    with pytest.raises(RuntimeError):
        ctx.set("invalid:key", "value")

    with pytest.raises(RuntimeError):
        ctx.get("invalid:key")


def test_runtime_context_nested_keys():
    """Test nested key access in RuntimeContext."""
    ctx = RuntimeContext()

    # Test nested keys in agent scope
    ctx.set("agent:profile.name", "Alice")
    ctx.set("agent:profile.age", 30)
    assert ctx.get("agent:profile.name") == "Alice"
    assert ctx.get("agent:profile.age") == 30

    # Test nested keys in world scope
    ctx.set("world:sensor.temperature", 25)
    ctx.set("world:sensor.status", "active")
    assert ctx.get("world:sensor.temperature") == 25
    assert ctx.get("world:sensor.status") == "active"

    # Test nested keys in execution scope
    ctx.set("execution:status.code", 200)
    ctx.set("execution:status.message", "OK")
    assert ctx.get("execution:status.code") == 200
    assert ctx.get("execution:status.message") == "OK"


def test_resource_registry():
    """Test resource registry functionality."""
    ctx = RuntimeContext()

    # Register a resource
    ctx.resources.register("llm", "mock_llm")
    assert ctx.get("resource:llm") == "mock_llm"

    # Test getting non-existent resource
    with pytest.raises(RuntimeError):
        ctx.get("resource:nonexistent")

    # Test setting resource (should fail)
    with pytest.raises(RuntimeError):
        ctx.set("resource:llm", "new_llm")


def test_invalid_keys():
    """Test handling of invalid keys."""
    ctx = RuntimeContext()

    # Test un-scoped keys
    with pytest.raises(RuntimeError):
        ctx.get("unscoped_key")

    with pytest.raises(RuntimeError):
        ctx.set("unscoped_key", "value")

    # Test empty keys
    with pytest.raises(RuntimeError):
        ctx.get(":")

    with pytest.raises(RuntimeError):
        ctx.set(":", "value")
