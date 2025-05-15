"""Unit tests for the DANA language context."""

import pytest

from opendxa.dana.common.exceptions import StateError
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_set_and_get_variable():
    """Test setting and getting variables in different scopes."""
    ctx = SandboxContext()

    # Test private scope
    ctx.set("private.name", "Alice")
    assert ctx.get("private.name") == "Alice"

    # Test public scope
    ctx.set("public.weather", "sunny")
    assert ctx.get("public.weather") == "sunny"

    # Test system scope
    ctx.set("system.status", "running")
    assert ctx.get("system.status") == "running"


def test_get_nonexistent_variable():
    """Test getting a nonexistent variable."""
    ctx = SandboxContext()
    with pytest.raises(StateError):
        ctx.get("private.nonexistent")


def test_set_variable_invalid_scope():
    """Test setting a variable with an invalid scope."""
    ctx = SandboxContext()
    with pytest.raises(StateError):
        ctx.set("invalid.key", "value")


def test_set_variable_invalid_name():
    """Test setting a variable with an invalid name."""
    ctx = SandboxContext()
    with pytest.raises(StateError):
        ctx.set("private.", "value")  # Empty name
