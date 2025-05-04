"""Unit tests for the DANA language context."""

import pytest

from opendxa.dana.exceptions import StateError
from opendxa.dana.runtime.context import RuntimeContext


def test_set_and_get_variable():
    """Test setting and getting variables in different scopes."""
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


def test_get_nonexistent_variable():
    """Test getting a nonexistent variable."""
    ctx = RuntimeContext()
    with pytest.raises(StateError):
        ctx.get("private.nonexistent")


def test_set_variable_invalid_scope():
    """Test setting a variable with an invalid scope."""
    ctx = RuntimeContext()
    with pytest.raises(StateError):
        ctx.set("invalid.key", "value")


def test_set_variable_invalid_name():
    """Test setting a variable with an invalid name."""
    ctx = RuntimeContext()
    with pytest.raises(StateError):
        ctx.set("private.", "value")  # Empty name
