"""Unit tests for the DANA language context."""

import pytest

from opendxa.dana.exceptions import RuntimeError
from opendxa.dana.runtime.runtime_context import RuntimeContext


def test_set_and_get_variable():
    """Test setting and getting variables in different scopes."""
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


def test_get_nonexistent_variable():
    """Test getting a nonexistent variable."""
    ctx = RuntimeContext()
    assert ctx.get("agent:nonexistent") is None


def test_set_variable_invalid_scope():
    """Test setting a variable with an invalid scope."""
    ctx = RuntimeContext()
    with pytest.raises(RuntimeError):
        ctx.set("invalid:key", "value")


def test_set_variable_invalid_name():
    """Test setting a variable with an invalid name."""
    ctx = RuntimeContext()
    with pytest.raises(RuntimeError):
        ctx.set("agent:", "value")  # Empty name
