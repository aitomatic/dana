"""Tests for the DANA runtime context."""

import pytest

from opendxa.dana.common.exceptions import StateError
from opendxa.dana.runtime.context import ExecutionStatus, RuntimeContext


def test_runtime_context_scopes():
    """Test scope-based access in RuntimeContext."""
    ctx = RuntimeContext()

    # Test local scope (unscoped variables)
    ctx.set("name", "Alice")
    assert ctx.get("name") == "Alice"
    assert ctx.get("local.name") == "Alice"
    # Dotted local variable names are not allowed
    with pytest.raises(StateError):
        ctx.set("foo.bar", 123)

    # Test private scope
    ctx.set("private.name", "Bob")
    assert ctx.get("private.name") == "Bob"

    # Test public scope
    ctx.set("public.weather", "sunny")
    assert ctx.get("public.weather") == "sunny"

    # Test system scope
    ctx.set("system.status", "running")
    assert ctx.get("system.status") == "running"


def test_runtime_context_nested_keys():
    """Test nested key access in RuntimeContext."""
    ctx = RuntimeContext()

    # Test local scope does not allow nested keys
    with pytest.raises(StateError):
        ctx.set("profile.name", "Alice")
    with pytest.raises(StateError):
        ctx.set("profile.age", 30)

    # Test private scope allows nested keys
    ctx.set("private.profile.name", "Bob")
    ctx.set("private.profile.age", 35)
    assert ctx.get("private.profile.name") == "Bob"
    assert ctx.get("private.profile.age") == 35

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


def test_parent_context_inheritance():
    """Test inheritance from parent context."""
    # Create parent context
    parent = RuntimeContext()
    parent.set("private.name", "Parent")
    parent.set("public.weather", "sunny")
    parent.set("system.status", "running")
    parent.set("local_var", "parent_local")  # Local variables don't inherit

    # Create child context
    child = RuntimeContext(parent=parent)

    # Test inheritance of shared scopes
    assert child.get("private.name") == "Parent"
    assert child.get("public.weather") == "sunny"
    assert child.get("system.status") == "running"

    # Test local scope is fresh
    with pytest.raises(StateError):
        child.get("local_var")

    # Test modifications don't affect parent
    child.set("private.name", "Child")
    assert child.get("private.name") == "Child"
    assert parent.get("private.name") == "Parent"


def test_from_dict_with_base_context():
    """Test creating RuntimeContext from dictionary with base context override."""
    # Create base context with some values
    base = RuntimeContext()
    base.set("private.name", "Bob")
    base.set("public.weather", "rainy")
    base.set("private.other", "base_value")

    # Create data that will be overridden by base context
    data = {
        "private.name": "Alice",  # Will override base
        "public.weather": "sunny",  # Will override base
        "private.new": "new_value",  # Will be kept
        "local_var": "local_value",  # Goes to local scope
    }

    ctx = RuntimeContext.from_dict(data, base)

    # Base context values should take precedence for shared scopes
    assert ctx.get("private.name") == "Alice"
    assert ctx.get("public.weather") == "sunny"

    # Base context values should be included
    assert ctx.get("private.other") == "base_value"

    # New values from data should be included
    assert ctx.get("private.new") == "new_value"
    assert ctx.get("local_var") == "local_value"


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


def test_shared_global_modifications():
    """Test that modifications to global scopes are shared across contexts."""
    # Create parent context
    parent = RuntimeContext()
    parent.set("private.name", "Parent")
    parent.set("public.weather", "sunny")
    parent.set("system.status", "running")
    parent.set("local_var", "parent_local")  # Local variables don't share

    # Create child context
    child = RuntimeContext(parent=parent)

    # Test initial state
    assert child.get("private.name") == "Parent"
    assert child.get("public.weather") == "sunny"
    assert child.get("system.status") == "running"

    # Modify global scopes in child
    child.set("private.name", "Child")
    child.set("public.weather", "rainy")
    child.set("system.status", "stopped")

    # Verify changes are shared with parent
    assert parent.get("private.name") == "Child"
    assert parent.get("public.weather") == "rainy"
    assert parent.get("system.status") == "stopped"

    # Verify local scope is not shared
    child.set("local_var", "child_local")
    assert child.get("local_var") == "child_local"
    assert parent.get("local_var") == "parent_local"

    # Create another child context
    child2 = RuntimeContext(parent=parent)

    # Verify child2 sees the same global state
    assert child2.get("private.name") == "Child"
    assert child2.get("public.weather") == "rainy"
    assert child2.get("system.status") == "stopped"

    # Modify global scopes in child2
    child2.set("private.name", "Child2")
    child2.set("public.weather", "cloudy")

    # Verify changes are shared with all contexts
    assert parent.get("private.name") == "Child2"
    assert parent.get("public.weather") == "cloudy"
    assert child.get("private.name") == "Child2"
    assert child.get("public.weather") == "cloudy"
