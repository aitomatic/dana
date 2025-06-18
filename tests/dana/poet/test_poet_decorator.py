"""
Tests for the POET decorator functionality.

This module tests the POET decorator's ability to:
1. Register functions with the POET registry
2. Execute functions with proper context
3. Handle function metadata
4. Support function overwriting
5. Handle errors appropriately
6. Handle namespace
7. Handle decorator chaining
"""

import pytest

from opendxa.dana.sandbox.dana_sandbox import DanaSandbox


def get_context(result):
    """Helper function to get the context from an ExecutionResult."""
    assert result.final_context is not None, f"Execution failed or context missing: {result.error}"
    return result.final_context


@pytest.fixture
def sandbox():
    """Create a DanaSandbox instance with proper initialization."""
    sandbox = DanaSandbox()
    sandbox._ensure_initialized()  # Force initialization
    return sandbox


def test_basic_poet_decorator(sandbox):
    """Test basic POET decorator functionality."""
    result = sandbox.run("tests/dana/poet/test_poet_decorator.na")
    context = get_context(result)
    assert result.success
    assert context.get("test_basic")(5) == 10


def test_poet_decorator_with_context(sandbox):
    """Test POET decorator with context handling."""
    result = sandbox.run("tests/dana/poet/test_poet_decorator.na")
    context = get_context(result)
    assert result.success
    func = context.get("test_context")
    assert func(5) == 10
    assert context.get("test_value") == 5


def test_poet_decorator_metadata(sandbox):
    """Test POET decorator metadata preservation."""
    result = sandbox.run("tests/dana/poet/test_poet_decorator.na")
    context = get_context(result)
    assert result.success
    func = context.get("test_metadata")
    assert hasattr(func, "_poet_metadata")
    assert func._poet_metadata["domain"] == "test_domain"
    assert func._poet_metadata["retries"] == 3
    assert func._poet_metadata["timeout"] == 5


def test_poet_decorator_overwrite(sandbox):
    """Test POET decorator function overwriting."""
    result = sandbox.run("tests/dana/poet/test_poet_decorator.na")
    context = get_context(result)
    assert result.success
    assert context.get("test_overwrite")(5) == 15


def test_poet_decorator_error_handling(sandbox):
    """Test POET decorator error handling."""
    result = sandbox.run("tests/dana/poet/test_poet_decorator.na")
    context = get_context(result)
    func = context.get("test_error")
    with pytest.raises(ValueError) as exc_info:
        func(5)
    assert str(exc_info.value) == "Test error"


def test_poet_decorator_namespace(sandbox):
    """Test POET decorator namespace handling."""
    result = sandbox.run("tests/dana/poet/test_poet_decorator.na")
    context = get_context(result)
    assert result.success
    assert context.get("custom.test_namespace")(5) == 10


def test_poet_decorator_chain(sandbox):
    """Test chaining multiple POET decorators."""
    result = sandbox.run("tests/dana/poet/test_poet_decorator.na")
    context = get_context(result)
    assert result.success
    func = context.get("test_chain")
    assert hasattr(func, "_poet_metadata")
    assert "test_domain" in func._poet_metadata["domains"]
    assert "test_domain2" in func._poet_metadata["domains"]
    assert func(5) == 10
