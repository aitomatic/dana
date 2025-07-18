"""
Tests for POET Perceive Phase.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.frameworks.poet.core.types import POETConfig
from dana.frameworks.poet.phases.perceive import PerceivePhase


def test_perceive_phase_initialization():
    """Test PerceivePhase initialization."""
    config = POETConfig()
    phase = PerceivePhase(config)
    assert phase.config == config


def test_perceive_basic_validation():
    """Test basic input validation."""
    config = POETConfig()
    phase = PerceivePhase(config)

    # Test valid inputs
    processed_args, processed_kwargs, context = phase.perceive((1, 2), {"a": 3})
    assert processed_args == (1, 2)
    assert processed_kwargs == {"a": 3}
    assert context["domain"] is None

    # Test None in args - should raise ValueError
    with pytest.raises(ValueError, match="Positional argument 1 cannot be None"):
        phase.perceive((1, None), {"a": 3})

    # Test None in kwargs - should raise ValueError
    with pytest.raises(ValueError, match="Keyword argument 'a' cannot be None"):
        phase.perceive((1, 2), {"a": None})


def test_perceive_domain_processing():
    """Test domain-specific input processing."""
    config = POETConfig(domain="test_domain")
    phase = PerceivePhase(config)

    processed_args, processed_kwargs, context = phase.perceive((1, 2), {"a": 3})
    assert processed_args == (1, 2)
    assert processed_kwargs == {"a": 3}
    assert context["domain"] == "test_domain"


def test_perceive_context_gathering():
    """Test context gathering."""
    config = POETConfig(
        domain="test_domain",
        retries=3,
        timeout=30.0,
        enable_training=True,
    )
    phase = PerceivePhase(config)

    processed_args, processed_kwargs, context = phase.perceive((1, 2), {"a": 3})
    assert processed_args == (1, 2)
    assert processed_kwargs == {"a": 3}
    assert context == {
        "domain": "test_domain",
        "retries": 3,
        "timeout": 30.0,
    }


def test_perceive_error_handling():
    """Test error handling in perceive phase."""
    config = POETConfig()
    phase = PerceivePhase(config)

    # Mock a failure in domain processing
    def mock_process_domain_inputs(args, kwargs, context):
        raise ValueError("Test error")

    phase._process_domain_inputs = mock_process_domain_inputs
    config.domain = "test_domain"  # Enable domain processing

    with pytest.raises(ValueError, match="Test error"):
        phase.perceive((1, 2), {"a": 3})


def test_validate_inputs_method():
    """Test the _validate_inputs method."""
    config = POETConfig()
    phase = PerceivePhase(config)

    # Test valid inputs
    phase._validate_inputs((1, 2), {"a": 3})

    # Test None in args
    with pytest.raises(ValueError, match="Positional argument 1 cannot be None"):
        phase._validate_inputs((1, None), {"a": 3})

    # Test None in kwargs
    with pytest.raises(ValueError, match="Keyword argument 'a' cannot be None"):
        phase._validate_inputs((1, 2), {"a": None})
