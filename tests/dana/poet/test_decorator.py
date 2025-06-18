"""
Tests for POET decorator implementation.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import json
from datetime import datetime

from opendxa.dana.poet.decorator import POETDecorator, POETMetadata, poet


def test_poet_decorator_initialization():
    """Test basic decorator initialization."""

    @poet(domain="test_domain")
    def test_func(x: int) -> int:
        return x * 2

    assert isinstance(test_func, POETDecorator)
    assert test_func.metadata.config is not None
    assert test_func.metadata.config.domain == "test_domain"


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


def test_enhanced_version_generation(tmp_path, monkeypatch):
    """Test enhanced version generation."""

    # Mock transpiler
    def mock_transpile(*args, **kwargs):
        return {
            "code": "def enhanced_func(x): return x * 2",
            "metadata": {"version": 1, "domain": "test_domain", "timestamp": datetime.now().isoformat()},
        }

    monkeypatch.setattr("opendxa.dana.poet.transpiler.PoetTranspiler.transpile", mock_transpile)

    @poet(domain="test_domain")
    def test_func(x: int) -> int:
        return x * 2

    # Should generate enhanced version
    result = test_func(5)
    assert result == 10

    # Check files were created
    enhanced_path = test_func.metadata.enhanced_path
    assert enhanced_path.exists()
    assert enhanced_path.read_text() == "def enhanced_func(x): return x * 2"

    # Check metadata
    metadata_path = enhanced_path.parent / "metadata.json"
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text())
    assert metadata["domain"] == "test_domain"
    assert metadata["version"] == 1


def test_enhanced_version_regeneration(tmp_path, monkeypatch):
    """Test enhanced version regeneration when original function changes."""

    # Mock transpiler
    def mock_transpile(*args, **kwargs):
        return {
            "code": "def enhanced_func(x): return x * 2",
            "metadata": {"version": 1, "domain": "test_domain", "timestamp": datetime.now().isoformat()},
        }

    monkeypatch.setattr("opendxa.dana.poet.transpiler.PoetTranspiler.transpile", mock_transpile)

    @poet(domain="test_domain")
    def test_func(x: int) -> int:
        return x * 2

    # Generate initial version
    test_func(5)

    # Modify original function
    test_func.func.__code__ = (lambda x: x * 3).__code__

    # Should regenerate enhanced version
    result = test_func(5)
    assert result == 15


def test_fallback_to_original(tmp_path, monkeypatch):
    """Test fallback to original function when enhancement fails."""

    # Mock transpiler to fail
    def mock_transpile(*args, **kwargs):
        raise RuntimeError("Transpilation failed")

    monkeypatch.setattr("opendxa.dana.poet.transpiler.PoetTranspiler.transpile", mock_transpile)

    @poet(domain="test_domain")
    def test_func(x: int) -> int:
        return x * 2

    # Should fall back to original function
    result = test_func(5)
    assert result == 10


def test_decorator_with_arguments():
    """Test decorator with additional arguments."""

    @poet(domain="test", retries=5, timeout=60.0, enable_training=True)
    def test_func(x: int) -> int:
        return x * 2

    # Verify decorator instance
    assert isinstance(test_func, POETDecorator)
    assert test_func.metadata.config is not None
    assert test_func.metadata.config.domain == "test"
    assert test_func.metadata.config.retries == 5
    assert test_func.metadata.config.timeout == 60.0
    assert test_func.metadata.config.enable_training is True
    assert test_func.metadata.config.optimize_for is None
    assert test_func.metadata.config.enable_monitoring is True

    # Test function execution
    result = test_func(5)
    assert result == 10


def test_decorator_preserves_function_metadata():
    """Test that decorator preserves function metadata."""

    @poet(domain="test_domain")
    def test_func(x: int) -> int:
        """Test function docstring."""
        return x * 2

    assert test_func.func.__name__ == "test_func"
    assert test_func.func.__doc__ == "Test function docstring."
    assert test_func.func.__annotations__ == {"x": int, "return": int}


def test_general_decorator_support():
    """Test that general decorators are applied in bottom-up order."""
    from pathlib import Path

    from opendxa.dana.sandbox.dana_sandbox import DanaSandbox

    # Create a temporary .na file with two decorators
    test_file = Path("tmp/test_general_decorator.na")
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

    # Run the file using DanaSandbox
    sandbox = DanaSandbox()
    result = sandbox.run(test_file)

    # Check execution completed successfully
    assert result.success is True
    assert result.error is None

    # Check that the wrapped function is registered in the context
    context = result.final_context
    assert context is not None
    foo_func = context.get("local.foo")
    assert foo_func is not None
    assert hasattr(foo_func, "__name__")
    assert foo_func.__name__ == "foo"
    assert hasattr(foo_func, "execute")  # Verify it's a SandboxFunction
