"""
Tests for POET decorator as a pure Dana language feature.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.frameworks.poet.decorator import POETMetadata, poet
from dana.frameworks.poet.types import POETConfig


@pytest.mark.poet
def test_poet_decorator_factory():
    """Test POET decorator factory creates proper decorator function."""
    decorator_func = poet(domain="test_domain")

    # Should return a callable decorator function
    assert callable(decorator_func)


@pytest.mark.poet
def test_poet_decorator_with_dana_parameters():
    """Test POET decorator with Dana-relevant parameters."""
    decorator_func = poet(domain="healthcare", retries=3, enable_training=True)

    # Should return a callable decorator function
    assert callable(decorator_func)


@pytest.mark.poet
def test_poet_enhances_dana_function():
    """Test applying POET decorator to a Dana-like function."""

    # Simulate a Dana function
    def dana_func(x):
        """A simulated Dana function."""
        return x * 2

    dana_func.__name__ = "calculate"

    # Apply POET decorator
    decorator = poet(domain="math")
    enhanced_func = decorator(dana_func)

    # Test enhanced function works
    result = enhanced_func(5)
    assert result == 10

    # Check POET metadata is attached
    assert hasattr(enhanced_func, "_poet_config")
    assert enhanced_func._poet_config["domain"] == "math"
    assert enhanced_func._poet_config["retries"] == 1
    assert enhanced_func._poet_config["enable_training"]


@pytest.mark.poet
def test_poet_config_for_dana():
    """Test POETConfig works for Dana function configuration."""
    config = POETConfig(domain="data_processing", retries=2, enable_training=True)

    assert config.domain == "data_processing"
    assert config.retries == 2
    assert config.enable_training

    # Should be serializable for Dana runtime
    config_dict = config.dict()
    assert isinstance(config_dict, dict)
    assert config_dict["domain"] == "data_processing"


@pytest.mark.poet
def test_poet_metadata_for_dana():
    """Test POETMetadata for Dana function tracking."""
    config = POETConfig(domain="test_domain", retries=2)
    metadata = POETMetadata("test_function", config)

    assert metadata.function_name == "test_function"
    assert metadata.version == 1
    assert metadata["domains"] == ["test_domain"]
    assert metadata["retries"] == 2


@pytest.mark.poet
def test_poet_phases_in_dana_context():
    """Test that POET phases execute in Dana function context."""

    # Track function calls to verify POET phases
    call_log = []

    def dana_func(x):
        call_log.append(f"dana_function_executed_with_{x}")
        return x * 3

    dana_func.__name__ = "process_data"

    # Apply POET decorator
    decorator = poet(domain="data_processing")
    enhanced_func = decorator(dana_func)

    # Execute enhanced function
    result = enhanced_func(4)

    # Verify correct result
    assert result == 12

    # Verify original Dana function was called
    assert "dana_function_executed_with_4" in call_log

    # Verify function metadata preserved
    assert enhanced_func.__name__ == "process_data"


@pytest.mark.poet
def test_poet_error_handling_in_dana():
    """Test POET error handling for Dana functions."""

    def failing_dana_func(x):
        raise ValueError("Dana function error")

    failing_dana_func.__name__ = "failing_operation"

    decorator = poet(domain="test", retries=1)
    enhanced_func = decorator(failing_dana_func)

    # Should propagate the error after retry logic
    with pytest.raises(ValueError, match="Dana function error"):
        enhanced_func(5)


@pytest.mark.poet
def test_poet_preserves_dana_function_identity():
    """Test that POET preserves Dana function identity and metadata."""

    def original_dana_func(a, b):
        """Original Dana function docstring."""
        return a + b

    original_dana_func.__name__ = "add_numbers"

    # Apply POET decorator
    decorator = poet(domain="arithmetic")
    enhanced_func = decorator(original_dana_func)

    # Check that Dana function identity is preserved
    assert enhanced_func.__name__ == "add_numbers"
    assert enhanced_func.__doc__ == "Original Dana function docstring."

    # Check POET configuration is accessible
    assert enhanced_func._poet_config["domain"] == "arithmetic"
