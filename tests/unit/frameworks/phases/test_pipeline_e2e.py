"""
End-to-end test for the POET pipeline: Perceive → Operate → Enforce

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.frameworks.poet.phases.enforce import EnforcePhase
from dana.frameworks.poet.phases.operate import OperatePhase
from dana.frameworks.poet.phases.perceive import PerceivePhase
from dana.frameworks.poet.types import POETConfig


def dummy_func(x, y):
    return x + y


def test_poet_pipeline_e2e_success():
    """Test the full POET pipeline with valid input and function."""
    config = POETConfig(domain="test", retries=2, timeout=10.0, enable_training=True)
    perceive = PerceivePhase(config)
    operate = OperatePhase(config)
    enforce = EnforcePhase(config)

    # Step 1: Perceive
    processed_args, processed_kwargs, context = perceive.perceive((2, 3), {})
    assert processed_args == (2, 3)
    assert processed_kwargs == {}

    # Step 2: Operate
    output = operate.operate(dummy_func, processed_args, processed_kwargs, context)
    assert output == 5

    # Step 3: Enforce
    result = enforce.enforce(output, context, expected_type=int)
    assert result == 5


def test_poet_pipeline_e2e_perceive_error():
    """Test the pipeline with invalid input (None in args)."""
    config = POETConfig(domain="test")
    perceive = PerceivePhase(config)

    # Step 1: Perceive (invalid input) - should raise ValueError
    with pytest.raises(ValueError, match="Positional argument 1 cannot be None"):
        perceive.perceive((1, None), {})


def test_poet_pipeline_e2e_operate_error():
    """Test the pipeline with a function that raises an error."""
    config = POETConfig(domain="test")
    perceive = PerceivePhase(config)
    operate = OperatePhase(config)

    def error_func(x, y):
        raise ValueError("Test error in operate phase")

    # Step 1: Perceive
    processed_args, processed_kwargs, context = perceive.perceive((2, 3), {})

    # Step 2: Operate (error) - should raise ValueError
    with pytest.raises(ValueError, match="Test error in operate phase"):
        operate.operate(error_func, processed_args, processed_kwargs, context)


def test_poet_pipeline_e2e_enforce_error():
    """Test the pipeline with an output type mismatch in Enforce phase."""
    config = POETConfig(domain="test")
    perceive = PerceivePhase(config)
    operate = OperatePhase(config)
    enforce = EnforcePhase(config)

    # Step 1: Perceive
    processed_args, processed_kwargs, context = perceive.perceive((2, 3), {})

    # Step 2: Operate
    output = operate.operate(dummy_func, processed_args, processed_kwargs, context)
    assert output == 5

    # Step 3: Enforce (expecting str, but got int) - should raise TypeError
    with pytest.raises(TypeError, match="Output type mismatch"):
        enforce.enforce(output, context, expected_type=str)
