"""Tests for DANA variable auto-scoping behavior."""

import pytest

from opendxa.dana.exceptions import StateError
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.executor.context_manager import ContextManager


def test_rhs_auto_scoping():
    """Test that right-hand side variables are properly auto-scoped."""
    context = RuntimeContext()
    manager = ContextManager(context)

    # Set up test variables in different scopes
    context.set("private.x", 10)
    context.set("public.y", 20)
    context.set("system.z", 30)

    # Test bare variable resolution (should check private first, then public, then system)
    assert manager.get_variable("x") == 10  # Should find private.x
    assert manager.get_variable("y") == 20  # Should find public.y
    assert manager.get_variable("z") == 30  # Should find system.z

    # Test explicit scope resolution (should use exact scope)
    assert manager.get_variable("private.x") == 10
    assert manager.get_variable("public.y") == 20
    assert manager.get_variable("system.z") == 30

    # Test variable not found in any scope
    with pytest.raises(StateError) as exc_info:
        manager.get_variable("nonexistent")
    assert "Variable not found: nonexistent" in str(exc_info.value)


def test_rhs_auto_scoping_precedence():
    """Test that RHS auto-scoping follows the correct precedence order."""
    context = RuntimeContext()
    manager = ContextManager(context)

    # Set up variables with same name in different scopes
    context.set("private.x", 10)
    context.set("public.x", 20)
    context.set("system.x", 30)

    # Should find private.x first
    assert manager.get_variable("x") == 10

    # Remove private.x, should find public.x
    context.set("private.x", None)
    assert manager.get_variable("x") == 20

    # Remove public.x, should find system.x
    context.set("public.x", None)
    assert manager.get_variable("x") == 30

    # Remove system.x, should raise error
    context.set("system.x", None)
    with pytest.raises(StateError) as exc_info:
        manager.get_variable("x")
    assert "Variable not found: x" in str(exc_info.value)


def test_rhs_auto_scoping_with_dotted_names():
    """Test that dotted variable names are handled correctly."""
    context = RuntimeContext()
    manager = ContextManager(context)

    # Set up nested variables
    context.set("private.config.value", 42)
    context.set("public.config.value", 100)

    # Dotted names should use exact scope
    assert manager.get_variable("private.config.value") == 42
    assert manager.get_variable("public.config.value") == 100

    # Bare dotted names should not be auto-scoped
    with pytest.raises(StateError) as exc_info:
        manager.get_variable("config.value")
    error_msg = str(exc_info.value)
    assert "Unknown scope: config" in error_msg
    assert all(scope in error_msg for scope in ["public", "private", "system"])


def test_rhs_auto_scoping_with_local_context():
    """Test that local context takes precedence over auto-scoping."""
    context = RuntimeContext()
    manager = ContextManager(context)

    # Set up variables in different contexts
    context.set("private.x", 10)
    local_context = {"x": 42}

    # Local context should take precedence
    assert manager.get_variable("x", local_context) == 42

    # Explicit scope should still work
    assert manager.get_variable("private.x", local_context) == 10
