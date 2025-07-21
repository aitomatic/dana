"""
Tests for POET Enforce Phase

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.frameworks.poet.core.types import POETConfig
from dana.frameworks.poet.enforce import EnforcePhase


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
    assert result == "test"

    # Test None output - should raise ValueError
    with pytest.raises(ValueError, match="Output cannot be None"):
        enforce_phase.enforce(None, {}, str)

    # Test type mismatch - should raise TypeError
    with pytest.raises(TypeError, match="Output type mismatch"):
        enforce_phase.enforce(123, {}, str)


def test_enforce_domain_rules(enforce_phase):
    """Test domain-specific enforcement."""
    result = enforce_phase.enforce("test", {})
    assert result == "test"


def test_enforce_post_processing(enforce_phase):
    """Test post-processing."""
    result = enforce_phase.enforce("test", {})
    assert result == "test"


def test_enforce_error_handling(enforce_phase):
    """Test error handling during enforcement."""
    # Test with invalid context - should still work as context is not validated
    result = enforce_phase.enforce("test", None)
    assert result == "test"


def test_validate_output_method(enforce_phase):
    """Test the _validate_output method."""
    # Test valid output
    enforce_phase._validate_output("test", str)
    enforce_phase._validate_output(123, int)
    enforce_phase._validate_output(1.23, float)

    # Test invalid type
    with pytest.raises(TypeError, match="Output type mismatch"):
        enforce_phase._validate_output(123, str)

    with pytest.raises(TypeError, match="Output type mismatch"):
        enforce_phase._validate_output("test", int)

    with pytest.raises(TypeError, match="Output type mismatch"):
        enforce_phase._validate_output("test", float)

    # Test None output
    with pytest.raises(ValueError, match="Output cannot be None"):
        enforce_phase._validate_output(None, str)
