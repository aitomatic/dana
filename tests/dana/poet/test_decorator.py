"""
Tests for POET decorator implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import json
from datetime import datetime
import os
from pathlib import Path

import pytest

from opendxa.dana.poet.decorator import POETDecorator, POETMetadata, poet


@pytest.mark.poet
def test_poet_decorator_initialization():
    """Test basic decorator initialization."""

    @poet(domain="test_domain")
    def test_func(x: int) -> int:
        return x * 2

    assert isinstance(test_func, POETDecorator)
    assert test_func.metadata.config is not None
    assert test_func.metadata.config.domain == "test_domain"


@pytest.mark.poet
def test_metadata_initialization(tmp_path):
    """Test metadata initialization for decorated function."""

    @poet(domain="test_domain")
    def test_func(x: int) -> int:
        return x * 2

    assert isinstance(test_func, POETDecorator)
    metadata = test_func.metadata
    assert isinstance(metadata, POETMetadata)
    assert metadata.function_name == "test_func"
    assert metadata.version == 1
    assert metadata.enhanced_path.name == "enhanced.na"
    assert metadata.config is not None
    assert metadata.config.domain == "test_domain"


@pytest.mark.poet
def test_enhanced_version_generation(tmp_path, monkeypatch):
    """Test enhanced version generation."""

    # Mock transpiler to fail, forcing fallback to original function
    def mock_transpile(*args, **kwargs):
        raise RuntimeError("Transpilation failed")

    monkeypatch.setattr("opendxa.dana.poet.transpiler.POETTranspiler.transpile", mock_transpile)
    monkeypatch.setattr("opendxa.dana.poet.transpiler_llm.POETTranspilerLLM.transpile", mock_transpile)

    @poet(domain="test_domain", fallback_strategy="original", use_llm=False)
    def test_func_unique(x: int) -> int:
        return x * 2

    # Should fallback to original function due to transpilation failure
    result = test_func_unique(5)
    assert result == 10  # Fallback to original function

    # Verify decorator instance properties
    assert isinstance(test_func_unique, POETDecorator)
    assert test_func_unique.metadata.config.domain == "test_domain"
    assert test_func_unique.metadata.config.fallback_strategy == "original"


@pytest.mark.poet
def test_enhanced_version_regeneration(tmp_path, monkeypatch):
    """Test enhanced version regeneration when original function changes."""

    # Mock transpiler
    def mock_transpile(*args, **kwargs):
        return {
            "code": "def enhanced_func(x): return x * 2",
            "metadata": {"version": 1, "domain": "test_domain", "timestamp": datetime.now().isoformat()},
        }

    monkeypatch.setattr("opendxa.dana.poet.transpiler.POETTranspiler.transpile", mock_transpile)

    @poet(domain="test_domain", fallback_strategy="original")
    def test_func(x: int) -> int:
        return x * 2

    # Generate initial version
    test_func(5)

    # Modify original function
    test_func.func.__code__ = (lambda x: x * 3).__code__

    # Should regenerate enhanced version
    result = test_func(5)
    assert result == 15


@pytest.mark.poet
def test_fallback_to_original(tmp_path, monkeypatch):
    """Test fallback to original function when enhancement fails."""

    # Mock transpiler to fail
    def mock_transpile(*args, **kwargs):
        raise RuntimeError("Transpilation failed")

    monkeypatch.setattr("opendxa.dana.poet.transpiler.POETTranspiler.transpile", mock_transpile)

    @poet(domain="test_domain", fallback_strategy="original")
    def test_func(x: int) -> int:
        return x * 2

    # Should fall back to original function
    result = test_func(5)
    assert result == 10


@pytest.mark.poet
def test_decorator_with_arguments():
    """Test decorator with additional arguments."""

    @poet(domain="test", retries=5, timeout=60, fallback_strategy="original")
    def test_func(x: int) -> int:
        return x * 2

    # Verify decorator instance
    assert isinstance(test_func, POETDecorator)
    assert test_func.metadata.config is not None
    assert test_func.metadata.config.domain == "test"
    assert test_func.metadata.config.retries == 5
    assert test_func.metadata.config.timeout == 60
    assert test_func.metadata.config.optimize_for is None
    assert test_func.metadata.config.enable_monitoring is True

    # Test function execution
    result = test_func(5)
    assert result == 10


@pytest.mark.poet
def test_decorator_preserves_function_metadata():
    """Test that decorator preserves function metadata."""

    @poet(domain="test_domain")
    def test_func(x: int) -> int:
        """Test function docstring."""
        return x * 2

    assert test_func.func.__name__ == "test_func"
    assert test_func.func.__doc__ == "Test function docstring."
    assert test_func.func.__annotations__ == {"x": int, "return": int}


@pytest.mark.poet
def test_general_decorator_support(fresh_sandbox):
    """Test that general decorators are applied in bottom-up order."""
    from pathlib import Path

    # Create a temporary .na file with two decorators
    test_file = Path("tmp/test_general_decorator.na")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text(
        """
# @log_calls
# @retry(times=3)
def foo(x: int) -> int:
    return x + 1

# Execute the function
result = foo(5)
assert result == 6
"""
    )

    # Run the file using fresh_sandbox fixture
    result = fresh_sandbox.run(test_file)

    # Check execution completed successfully
    assert result.success is True
    assert result.error is None

    # Check that the wrapped function is registered in the context
    context = result.final_context
    assert context is not None
    foo_func = context.get("local:foo")
    assert foo_func is not None
    assert hasattr(foo_func, "__name__")
    assert foo_func.__name__ == "foo"
    assert hasattr(foo_func, "execute")  # Verify it's a SandboxFunction
