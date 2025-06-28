"""
Tests for POET Enforce Phase

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from opendxa.dana.poet.phases.enforce import EnforcePhase, EnforceResult
from opendxa.dana.poet.types import POETConfig


@pytest.fixture
def enforce_phase():
    """Create a basic EnforcePhase instance."""
    config = POETConfig(domain="test")
    return EnforcePhase(config)


def test_enforce_phase_initialization():
    """Test EnforcePhase initialization."""
    config = POETConfig(domain="test")
    phase = EnforcePhase(config)
    assert phase.config == config
    assert phase.config.domain == "test"


def test_enforce_basic_validation(enforce_phase):
    """Test basic output validation."""
    # Test valid output
    result = enforce_phase.enforce("test", {}, str)
    assert result.is_valid
    assert result.output == "test"
    assert not result.validation_errors

    # Test None output
    result = enforce_phase.enforce(None, {}, str)
    assert not result.is_valid
    assert "Output cannot be None" in result.validation_errors

    # Test type mismatch
    result = enforce_phase.enforce(123, {}, str)
    assert not result.is_valid
    assert "Output type mismatch" in result.validation_errors[0]


def test_enforce_domain_rules(enforce_phase):
    """Test domain-specific enforcement."""
    result = enforce_phase.enforce("test", {})
    assert result.is_valid
    assert result.output == "test"


def test_enforce_post_processing(enforce_phase):
    """Test post-processing."""
    result = enforce_phase.enforce("test", {})
    assert result.is_valid
    assert result.output == "test"


def test_enforce_error_handling(enforce_phase):
    """Test error handling during enforcement."""
    # Test with invalid context
    result = enforce_phase.enforce("test", None)
    assert not result.is_valid
    assert "Context cannot be None" in result.validation_errors[0]


def test_validate_type(enforce_phase):
    """Test type validation."""
    # Test valid type
    assert enforce_phase.validate_type("test", str)
    assert enforce_phase.validate_type(123, int)
    assert enforce_phase.validate_type(1.23, float)

    # Test invalid type
    assert not enforce_phase.validate_type(123, str)
    assert not enforce_phase.validate_type("test", int)
    assert not enforce_phase.validate_type("test", float)


def test_validate_range(enforce_phase):
    """Test range validation."""
    # Test valid ranges
    assert enforce_phase.validate_range(5, min_val=0, max_val=10)
    assert enforce_phase.validate_range(5, min_val=0)
    assert enforce_phase.validate_range(5, max_val=10)
    assert enforce_phase.validate_range(5)

    # Test invalid ranges
    assert not enforce_phase.validate_range(5, min_val=10)
    assert not enforce_phase.validate_range(5, max_val=0)
    assert not enforce_phase.validate_range(5, min_val=10, max_val=0)


def test_enforce_result_error_handling():
    """Test EnforceResult error handling."""
    result = EnforceResult()
    assert result.is_valid
    assert not result.validation_errors

    # Add first error
    result.add_error("First error")
    assert not result.is_valid
    assert len(result.validation_errors) == 1
    assert result.validation_errors[0] == "First error"

    # Add second error
    result.add_error("Second error")
    assert not result.is_valid
    assert len(result.validation_errors) == 2
    assert result.validation_errors[1] == "Second error"
