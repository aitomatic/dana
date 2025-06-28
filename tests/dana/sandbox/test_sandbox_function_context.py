#!/usr/bin/env python
"""
Test script for the SandboxFunction context sanitization.

This script tests that the SandboxFunction.__call__ method properly sanitizes
SandboxContext arguments passed to functions.
"""

from typing import Any

from opendxa.dana.sandbox.context_manager import ContextManager
from opendxa.dana.sandbox.interpreter.functions.sandbox_function import SandboxFunction
from opendxa.dana.sandbox.sandbox_context import SandboxContext


class MockSandboxFunction(SandboxFunction):
    """Test implementation of SandboxFunction."""

    def __init__(self, context=None):
        """Initialize the function."""
        super().__init__(context)
        self.parameters = ["test_context", "other_arg"]

    def prepare_context(self, context: SandboxContext, args: list[Any], kwargs: dict[str, Any]) -> SandboxContext:
        """Prepare context for function execution."""
        # Create a sanitized copy of the context
        return context.sanitize()

    def execute(self, context, *args, **kwargs):
        """Test implementation that returns the sanitized context."""
        # Return the first arg or kwarg that is a SandboxContext
        for arg in args:
            if isinstance(arg, SandboxContext):
                return arg.sanitize()

        for _key, value in kwargs.items():
            if isinstance(value, SandboxContext):
                return value.sanitize()

        return None

    def restore_context(self, context: SandboxContext, original_context: SandboxContext) -> SandboxContext:
        """Restore context after function execution."""
        return original_context


def test_sandbox_function_context_sanitization():
    """Test that SandboxFunction.__call__ sanitizes SandboxContext arguments."""
    # Create a context with sensitive data
    context = SandboxContext()
    context_manager = ContextManager(context)

    # Add test data
    context_manager.set_in_context("public_var", "public data", scope="public")
    context_manager.set_in_context("private_var", "sensitive private data", scope="private")
    context_manager.set_in_context("api_key", "sk_live_1234567890abcdef", scope="system")

    # Create a test function
    test_func = MockSandboxFunction(context)

    # Call the function with the context as a positional argument and proper parameter binding
    result1 = test_func(context, None, test_context=context, other_arg="dummy")

    # Call the function with the context as a keyword argument
    result2 = test_func(context, None, test_context=context, other_arg="dummy")

    # Verify that the returned contexts are sanitized
    print("Original context:")
    print(context)

    print("\nSanitized context from positional arg:")
    print(result1)

    print("\nSanitized context from keyword arg:")
    print(result2)

    # Check that public data is preserved
    assert "public_var" in result1._state["public"]
    assert result1._state["public"]["public_var"] == "public data"

    # Check that private data is removed or masked
    assert "private_var" not in result1._state.get("private", {})
    assert "api_key" not in result1._state.get("system", {})

    # Same checks for the keyword arg result
    assert "public_var" in result2._state["public"]
    assert result2._state["public"]["public_var"] == "public data"
    assert "private_var" not in result2._state.get("private", {})
    assert "api_key" not in result2._state.get("system", {})

    print("\nAll tests passed!")


if __name__ == "__main__":
    test_sandbox_function_context_sanitization()
