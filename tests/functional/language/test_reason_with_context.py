#!/usr/bin/env python
"""
Test reason function with user context in Dana language.
"""

from dana.core.lang.dana_sandbox import DanaSandbox


def test_reason_with_context():
    """Test that reason function works with user context."""
    sandbox = DanaSandbox()

    # Run the Dana test file
    result = sandbox.run_file("tests/functional/language/test_reason_with_context.na")

    # Verify that all tests completed successfully
    assert result.success
    assert result.result is not None
    assert isinstance(result.result, dict)

    # Check that all test results are present
    expected_keys = ["basic", "multiple", "nested", "empty", "no_context"]
    for key in expected_keys:
        assert key in result.result, f"Missing test result for {key}"
        assert result.result[key] is not None, f"Test result for {key} is None"

    # Verify that the results are valid (reason function can return strings, numbers, etc.)
    for key, value in result.result.items():
        # Reason function can return various types depending on the LLM response
        assert isinstance(value, str | int | float | dict | list), f"Test result for {key} has unexpected type: {type(value)}"
        assert len(str(value)) > 0, f"Test result for {key} is empty"


def test_reason_context_backward_compatibility():
    """Test that reason function still works without context parameter."""
    sandbox = DanaSandbox()

    # Test basic reason call without context
    result = sandbox.eval("reason('What is 2 + 2?')")

    assert result.success
    assert result.result is not None
    # Note: The result might be a number (4) or a string depending on the LLM response
    assert isinstance(result.result, str | int | float)
    assert len(str(result.result)) > 0


def test_reason_with_empty_context():
    """Test that reason function works with empty context dict."""
    sandbox = DanaSandbox()

    # Test reason call with empty context
    result = sandbox.eval("reason('What is 2 + 2?', context={})")

    assert result.success
    assert result.result is not None
    # Note: The result might be a number (4) or a string depending on the LLM response
    assert isinstance(result.result, str | int | float)
    assert len(str(result.result)) > 0


def test_reason_with_simple_context():
    """Test that reason function works with simple context."""
    sandbox = DanaSandbox()

    # Test reason call with simple context
    result = sandbox.eval("reason('What are the numbers?', context={'numbers': [5, 3]})")

    assert result.success
    assert result.result is not None
    assert isinstance(result.result, str)
    assert len(result.result) > 0

    # Verify that the context was merged correctly by checking the final context
    assert "numbers" in result.final_context.get_scope("local")
    assert result.final_context.get("local:numbers") == [5, 3]
