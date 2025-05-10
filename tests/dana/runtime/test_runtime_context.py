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

    # Test public scope
    ctx.set("public.weather", "sunny")
    assert ctx.get("public.weather") == "sunny"

    # Test system scope
    ctx.set("system.status", "running")
    assert ctx.get("system.status") == "running"


def test_runtime_context_nested_keys():
    """Test nested key access in RuntimeContext."""
    ctx = RuntimeContext()

    # Test nested keys in private scope
    ctx.set("private.profile.name", "Alice")
    ctx.set("private.profile.age", 30)
    assert ctx.get("private.profile.name") == "Alice"
    assert ctx.get("private.profile.age") == 30

    # Test nested keys in public scope
    ctx.set("public.location.city", "San Francisco")
    assert ctx.get("public.location.city") == "San Francisco"

    # Test nested keys in system scope
    ctx.set("system.history.last_action", "completed")
    assert ctx.get("system.history.last_action") == "completed"


def test_execution_state():
    """Test execution state management."""
    ctx = RuntimeContext()

    # Test initial state
    assert ctx.get_execution_status() == ExecutionStatus.IDLE

    # Test execution history
    ctx.add_execution_history({"action": "test"})
    history = ctx.get("system.history")
    assert len(history) == 1
    assert history[0]["action"] == "test"
    assert "timestamp" in history[0]

    # Test status update
    ctx.set_execution_status(ExecutionStatus.RUNNING)
    assert ctx.get_execution_status() == ExecutionStatus.RUNNING

    # Test reset
    ctx.reset_execution_state()
    assert ctx.get_execution_status() == ExecutionStatus.IDLE
    assert not ctx.get("system.history")


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


def test_from_dict_basic():
    """Test creating RuntimeContext from dictionary without base context."""
    data = {
        "private.name": "Alice",
        "public.weather": "sunny",
        "system.status": "running",
        "unscoped": "value",  # Should go to private scope
    }

    ctx = RuntimeContext.from_dict(data)

    # Test scoped variables
    assert ctx.get("private.name") == "Alice"
    assert ctx.get("public.weather") == "sunny"
    assert ctx.get("system.status") == "running"

    # Test unscoped variable went to private scope
    assert ctx.get("private.unscoped") == "value"


def test_from_dict_with_base_context():
    """Test creating RuntimeContext from dictionary with base context override."""
    # Create base context with some values
    base = RuntimeContext()
    base.set("private.name", "Bob")
    base.set("public.weather", "rainy")
    base.set("private.other", "base_value")

    # Create data that will be overridden by base context
    data = {
        "private.name": "Alice",  # Will be overridden by base
        "public.weather": "sunny",  # Will be overridden by base
        "private.new": "new_value",  # Will be kept
    }

    ctx = RuntimeContext.from_dict(data, base)

    # Base context values should take precedence
    assert ctx.get("private.name") == "Bob"
    assert ctx.get("public.weather") == "rainy"

    # Base context values should be included
    assert ctx.get("private.other") == "base_value"

    # New values from data should be included
    assert ctx.get("private.new") == "new_value"


def test_from_dict_resources():
    """Test that resources are copied from base context."""
    # Create base context with a resource
    base = RuntimeContext()
    resource = {"type": "test", "value": 42}
    base.register_resource("test_resource", resource)

    # Create new context with base
    ctx = RuntimeContext.from_dict({}, base)

    # Resource should be available
    assert ctx.get_resource("test_resource") == resource
    assert "test_resource" in ctx.list_resources()


def test_from_dict_empty():
    """Test creating RuntimeContext from empty dictionary."""
    # Test without base context
    ctx1 = RuntimeContext.from_dict({})
    assert ctx1.get_execution_status() == ExecutionStatus.IDLE

    # Test with base context
    base = RuntimeContext()
    base.set("private.name", "Bob")
    ctx2 = RuntimeContext.from_dict({}, base)
    assert ctx2.get("private.name") == "Bob"
