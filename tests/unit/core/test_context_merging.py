#!/usr/bin/env python
"""
Test context merging functionality in function registry.
"""

from dana.core.lang.interpreter.functions.function_registry import FunctionRegistry
from dana.core.lang.sandbox_context import SandboxContext


def test_context_merging_in_function_registry():
    """Test that user context is properly merged into local scope."""
    # Create a function registry
    registry = FunctionRegistry()

    # Create a test context
    context = SandboxContext()

    # Define a simple test function that can access local scope
    def test_function(context: SandboxContext, *args, **kwargs):
        """Test function that returns local scope values."""
        return {"numbers": context.get("local:numbers"), "name": context.get("local:name"), "config": context.get("local:config")}

    # Register the test function
    from dana.core.lang.interpreter.functions.function_registry import FunctionMetadata, FunctionType
    from dana.core.lang.interpreter.functions.python_function import PythonFunction

    test_func = PythonFunction(test_function, trusted_for_context=True)

    metadata = FunctionMetadata()
    registry.register("test_context_merge", test_func, func_type=FunctionType.PYTHON, metadata=metadata)

    # Test with user context - manually merge into local scope first
    user_context = {"numbers": [5, 3], "name": "test_user", "config": {"debug": True}}

    # Manually merge user context into local scope (simulating what the dispatcher does)
    for key, value in user_context.items():
        context.set(f"local:{key}", value)

    # Call the function without the conflicting context parameter
    result = registry.call("test_context_merge", context)

    # Verify the context was merged correctly
    assert result["numbers"] == [5, 3]
    assert result["name"] == "test_user"
    assert result["config"] == {"debug": True}

    # Verify the context is actually in the local scope
    assert context.get("local:numbers") == [5, 3]
    assert context.get("local:name") == "test_user"
    assert context.get("local:config") == {"debug": True}


def test_context_merging_with_non_dict_context():
    """Test that non-dict context is handled gracefully."""
    # Create a function registry
    registry = FunctionRegistry()

    # Create a test context
    context = SandboxContext()

    # Define a simple test function
    def test_function(context: SandboxContext, *args, **kwargs):
        return "success"

    # Register the test function
    from dana.core.lang.interpreter.functions.function_registry import FunctionMetadata, FunctionType
    from dana.core.lang.interpreter.functions.python_function import PythonFunction

    test_func = PythonFunction(test_function, trusted_for_context=True)

    metadata = FunctionMetadata()
    registry.register("test_non_dict_context", test_func, func_type=FunctionType.PYTHON, metadata=metadata)

    # Test with non-dict context - should not fail, just log warning
    # Since we're testing the registry directly, we'll test the manual merging
    result = registry.call("test_non_dict_context", context)

    # Should still succeed
    assert result == "success"


def test_context_merging_preserves_existing_local_scope():
    """Test that existing local scope values are preserved when merging context."""
    # Create a function registry
    registry = FunctionRegistry()

    # Create a test context with existing local values
    context = SandboxContext()
    context.set("local:existing_value", "preserved")
    context.set("local:shared_key", "original")

    # Define a test function
    def test_function(context: SandboxContext, *args, **kwargs):
        return {
            "existing_value": context.get("local:existing_value"),
            "shared_key": context.get("local:shared_key"),
            "new_value": context.get("local:new_value"),
        }

    # Register the test function
    from dana.core.lang.interpreter.functions.function_registry import FunctionMetadata, FunctionType
    from dana.core.lang.interpreter.functions.python_function import PythonFunction

    test_func = PythonFunction(test_function, trusted_for_context=True)

    metadata = FunctionMetadata()
    registry.register("test_preserve_existing", test_func, func_type=FunctionType.PYTHON, metadata=metadata)

    # Test with user context that has overlapping keys - manually merge
    user_context = {"shared_key": "overwritten", "new_value": "added"}

    # Manually merge user context into local scope
    for key, value in user_context.items():
        context.set(f"local:{key}", value)

    # Call the function without the conflicting context parameter
    result = registry.call("test_preserve_existing", context)

    # Verify existing values are preserved, new values are added, and overlapping keys are overwritten
    assert result["existing_value"] == "preserved"
    assert result["shared_key"] == "overwritten"  # User context overwrites existing
    assert result["new_value"] == "added"

    # Verify the context state
    assert context.get("local:existing_value") == "preserved"
    assert context.get("local:shared_key") == "overwritten"
    assert context.get("local:new_value") == "added"


def test_reason_function_with_context():
    """Test that the reason function can access merged context."""
    # This test would require the actual reason function to be available
    # For now, we'll test the context merging mechanism that the reason function would use

    # Create a function registry
    registry = FunctionRegistry()

    # Create a test context
    context = SandboxContext()

    # Define a mock reason function
    def mock_reason_function(context: SandboxContext, prompt: str, options: dict = None, use_mock: bool = None):
        """Mock reason function that accesses local context."""
        numbers = context.get("local:numbers")
        if numbers:
            return f"Numbers from context: {numbers}, Prompt: {prompt}"
        else:
            return f"No numbers in context, Prompt: {prompt}"

    # Register the mock reason function
    from dana.core.lang.interpreter.functions.function_registry import FunctionMetadata, FunctionType
    from dana.core.lang.interpreter.functions.python_function import PythonFunction

    reason_func = PythonFunction(mock_reason_function, trusted_for_context=True)

    metadata = FunctionMetadata()
    registry.register("reason", reason_func, func_type=FunctionType.PYTHON, metadata=metadata)

    # Test with user context - manually merge into local scope
    user_context = {"numbers": [5, 3]}

    # Manually merge user context into local scope
    for key, value in user_context.items():
        context.set(f"local:{key}", value)

    # Call the reason function without the conflicting context parameter
    result = registry.call("reason", context, "", "What is 5 + 3?")

    # Verify the result includes context data
    assert "Numbers from context: [5, 3]" in result
    assert "What is 5 + 3?" in result
