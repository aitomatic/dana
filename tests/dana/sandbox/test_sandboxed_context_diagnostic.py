#!/usr/bin/env python
"""
Diagnostic test for the get_sandboxed_context method.
"""

import sys

from opendxa.dana.sandbox.context_manager import ContextManager
from opendxa.dana.sandbox.sandbox_context import SandboxContext


def test_sandboxed_context():
    """Test the get_sandboxed_context method."""
    # Create a context with data in various scopes
    context = SandboxContext()
    context_manager = ContextManager(context)

    # Add data to different scopes
    context_manager.set_in_context("test_local", "local value", scope="local")
    context_manager.set_in_context("test_public", "public value", scope="public")
    context_manager.set_in_context("test_private", "sensitive private data", scope="private")
    context_manager.set_in_context("test_system", "sensitive system data", scope="system")

    print("Original context scopes:", list(context_manager.context._state.keys()))

    # Get the sandboxed context
    sandboxed = context_manager.get_sanitized_context()

    print("Sandboxed context scopes:", list(sandboxed._state.keys()))

    # Check public and local data is preserved
    assert "local" in sandboxed._state, "Local scope should be preserved"
    assert sandboxed._state["local"]["test_local"] == "local value"
    print("✓ Local scope preserved")

    assert "public" in sandboxed._state, "Public scope should be preserved"
    assert sandboxed._state["public"]["test_public"] == "public value"
    print("✓ Public scope preserved")

    # Check sensitive scopes are removed
    assert "private" not in sandboxed._state, "Private scope should be removed"
    print("✓ Private scope removed")

    assert "system" not in sandboxed._state, "System scope should be removed"
    print("✓ System scope removed")

    # Check the original context is unchanged
    assert "private" in context_manager.context._state
    assert "system" in context_manager.context._state
    assert context_manager.context._state["private"]["test_private"] == "sensitive private data"
    assert context_manager.context._state["system"]["test_system"] == "sensitive system data"
    print("✓ Original context unchanged")

    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_sandboxed_context()
    sys.exit(0)
