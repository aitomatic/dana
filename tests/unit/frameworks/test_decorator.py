"""
Tests for POET decorator as a pure Dana language feature.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.frameworks.poet.core.decorator import POETMetadata, poet
from dana.frameworks.poet.core.types import POETConfig


@pytest.mark.poet
def test_poet_decorator_basic():
    """Test basic POET decorator functionality."""
    decorator_func = poet(domain="healthcare", retries=3)

    @decorator_func
    def test_function(x: int) -> int:
        return x * 2

    result = test_function(5)
    assert result == 10
    assert test_function._poet_config["domain"] == "healthcare"
    assert test_function._poet_config["retries"] == 3


@pytest.mark.poet
def test_poet_decorator_with_training():
    """Test POET decorator with training configuration."""
    decorator = poet(domain="math", train={"learning_rate": 0.1})

    @decorator
    def math_function(x: int) -> int:
        return x**2

    result = math_function(4)
    assert result == 16
    assert math_function._poet_config["train"]["learning_rate"] == 0.1


@pytest.mark.poet
def test_poet_config_creation():
    """Test POETConfig creation and serialization."""
    config = POETConfig(domain="data_processing", retries=2, train={"feedback_threshold": 0.8})

    assert config.domain == "data_processing"
    assert config.retries == 2
    assert config.train["feedback_threshold"] == 0.8


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
