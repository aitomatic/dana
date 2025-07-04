"""
Tests for POET Perceive Phase.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.frameworks.poet.phases.perceive import PerceivePhase, PerceiveResult
from dana.frameworks.poet.types import POETConfig


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
    result = phase.perceive((1, 2), {"a": 3})
    assert result.is_valid
    assert not result.validation_errors
    assert result.processed_args == (1, 2)
    assert result.processed_kwargs == {"a": 3}

    # Test None in args
    result = phase.perceive((1, None), {"a": 3})
    assert not result.is_valid
    assert len(result.validation_errors) == 1
    assert "Positional argument 1 cannot be None" in result.validation_errors

    # Test None in kwargs
    result = phase.perceive((1, 2), {"a": None})
    assert not result.is_valid
    assert len(result.validation_errors) == 1
    assert "Keyword argument 'a' cannot be None" in result.validation_errors


def test_perceive_domain_processing():
    """Test domain-specific input processing."""
    config = POETConfig(domain="test_domain")
    phase = PerceivePhase(config)

    result = phase.perceive((1, 2), {"a": 3})
    assert result.is_valid
    assert result.context["domain"] == "test_domain"


def test_perceive_context_gathering():
    """Test context gathering."""
    config = POETConfig(
        domain="test_domain",
        retries=3,
        timeout=30.0,
        enable_training=True,
    )
    phase = PerceivePhase(config)

    result = phase.perceive((1, 2), {"a": 3})
    assert result.is_valid
    assert result.context == {
        "domain": "test_domain",
        "retries": 3,
        "timeout": 30.0,
        "enable_training": True,
    }


def test_perceive_error_handling():
    """Test error handling in perceive phase."""
    config = POETConfig()
    phase = PerceivePhase(config)

    # Mock a failure in domain processing
    def mock_process_domain_inputs(result: PerceiveResult) -> None:
        raise ValueError("Test error")

    phase._process_domain_inputs = mock_process_domain_inputs
    config.domain = "test_domain"  # Enable domain processing

    result = phase.perceive((1, 2), {"a": 3})
    assert not result.is_valid
    assert len(result.validation_errors) == 1
    assert "Perceive phase error: Test error" in result.validation_errors


def test_perceive_result_error_handling():
    """Test PerceiveResult error handling."""
    result = PerceiveResult(
        processed_args=(),
        processed_kwargs={},
        context={},
        validation_errors=[],
    )

    # Test initial state
    assert result.is_valid
    assert not result.validation_errors

    # Test adding error
    result.add_error("Test error")
    assert not result.is_valid
    assert len(result.validation_errors) == 1
    assert "Test error" in result.validation_errors

    # Test adding multiple errors
    result.add_error("Another error")
    assert not result.is_valid
    assert len(result.validation_errors) == 2
    assert "Test error" in result.validation_errors
    assert "Another error" in result.validation_errors
