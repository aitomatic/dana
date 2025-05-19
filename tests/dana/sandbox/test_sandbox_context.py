"""
Test for the SandboxContext class with both dot and colon scope notation support.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from opendxa.dana.common.exceptions import StateError
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_sandbox_context_dot_notation():
    """Test using dot notation for scopes."""
    context = SandboxContext()

    # Set values with dot notation
    context.set("private.test", 42)
    context.set("public.weather", "sunny")
    context.set("system.config", {"debug": True})
    context.set("local.temp", 98.6)
    context.set("unscoped", "value")

    # Get values with dot notation
    assert context.get("private.test") == 42
    assert context.get("public.weather") == "sunny"
    assert context.get("system.config") == {"debug": True}
    assert context.get("local.temp") == 98.6
    assert context.get("unscoped") == "value"

    # Test default values
    assert context.get("nonexistent", "default") == "default"


def test_sandbox_context_colon_notation():
    """Test using colon notation for scopes."""
    context = SandboxContext()

    # Set values with colon notation
    context.set("private:test", 42)
    context.set("public:weather", "sunny")
    context.set("system:config", {"debug": True})
    context.set("local:temp", 98.6)

    # Get values with colon notation
    assert context.get("private:test") == 42
    assert context.get("public:weather") == "sunny"
    assert context.get("system:config") == {"debug": True}
    assert context.get("local:temp") == 98.6

    # Test default values
    assert context.get("nonexistent", "default") == "default"


def test_mixed_notation_access():
    """Test accessing values with different notation than they were set with."""
    context = SandboxContext()

    # Set with dot notation, get with colon notation
    context.set("private.test", 42)
    assert context.get("private:test") == 42

    # Set with colon notation, get with dot notation
    context.set("public:weather", "sunny")
    assert context.get("public.weather") == "sunny"


def test_local_variable_with_dots():
    """Test local variables containing dots."""
    context = SandboxContext()

    # This should be treated as a local variable
    context.set("not.a.valid.scope", "value")
    assert context.get("not.a.valid.scope") == "value"

    # This should not raise an error for local scope
    context.set("local:variable.with.dots", "value")
    assert context.get("local:variable.with.dots") == "value"

    # This should raise an error for local scope with dot notation
    with pytest.raises(StateError):
        context.set("local.variable.with.dots", "value")


def test_from_dict_with_mixed_notation():
    """Test creating a context from a dictionary with mixed notation."""
    data = {"private.x": 1, "public:y": 2, "system.z": 3, "local:w": 4, "unscoped": 5}

    context = SandboxContext.from_dict(data)

    # Test accessing with the same notation
    assert context.get("private.x") == 1
    assert context.get("public:y") == 2
    assert context.get("system.z") == 3
    assert context.get("local:w") == 4
    assert context.get("unscoped") == 5

    # Test accessing with alternate notation
    assert context.get("private:x") == 1
    assert context.get("public.y") == 2
