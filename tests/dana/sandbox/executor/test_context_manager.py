"""
Tests for the ContextManager class.
"""

from opendxa.dana.sandbox.context_manager import ContextManager
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class TestContextManager:
    """Test suite for the ContextManager class."""

    def test_get_sandboxed_context(self):
        """Test the get_sandboxed_context method."""
        # Create a context with data in various scopes
        context = SandboxContext()
        context_manager = ContextManager(context)

        # Add data to different scopes
        context_manager.set_in_context("test_local", "local value", scope="local")
        context_manager.set_in_context("test_public", "public value", scope="public")
        context_manager.set_in_context("test_private", "sensitive private data", scope="private")
        context_manager.set_in_context("test_system", "sensitive system data", scope="system")

        # Get the sandboxed context
        sandboxed = context_manager.get_sanitized_context()

        # Verify public and local data is preserved
        assert "local" in sandboxed._state
        assert sandboxed._state["local"]["test_local"] == "local value"

        assert "public" in sandboxed._state
        assert sandboxed._state["public"]["test_public"] == "public value"

        # Verify sensitive scopes are removed
        assert "private" not in sandboxed._state
        assert "system" not in sandboxed._state

        # Verify the original context is unchanged
        assert "private" in context_manager.context._state
        assert "system" in context_manager.context._state
        assert context_manager.context._state["private"]["test_private"] == "sensitive private data"
        assert context_manager.context._state["system"]["test_system"] == "sensitive system data"
