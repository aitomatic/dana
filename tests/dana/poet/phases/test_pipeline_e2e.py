"""
End-to-end test for the POET pipeline: Perceive → Operate → Enforce

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from opendxa.dana.poet.phases.enforce import EnforcePhase
from opendxa.dana.poet.phases.operate import OperatePhase
from opendxa.dana.poet.phases.perceive import PerceivePhase
from opendxa.dana.poet.types import POETConfig


def dummy_func(x, y):
    return x + y


def test_poet_pipeline_e2e_success():
    """Test the full POET pipeline with valid input and function."""
    config = POETConfig(domain="test", retries=2, timeout=10.0, enable_training=True)
    perceive = PerceivePhase(config)
    operate = OperatePhase(config)
    enforce = EnforcePhase(config)

    # Step 1: Perceive
    perceive_result = perceive.perceive((2, 3), {})
    assert perceive_result.is_valid
    assert perceive_result.processed_args == (2, 3)
    assert perceive_result.processed_kwargs == {}

    # Step 2: Operate
    operate_result = operate.operate(dummy_func, perceive_result.processed_args, perceive_result.processed_kwargs, perceive_result.context)
    assert operate_result.is_success
    assert operate_result.output == 5

    # Step 3: Enforce
    enforce_result = enforce.enforce(operate_result.output, perceive_result.context, expected_type=int)
    assert enforce_result.is_valid
    assert enforce_result.output == 5


def test_poet_pipeline_e2e_perceive_error():
    """Test the pipeline with invalid input (None in args)."""
    config = POETConfig(domain="test")
    perceive = PerceivePhase(config)
    operate = OperatePhase(config)
    enforce = EnforcePhase(config)

    # Step 1: Perceive (invalid input)
    perceive_result = perceive.perceive((1, None), {})
    assert not perceive_result.is_valid
    assert any("cannot be None" in e for e in perceive_result.validation_errors)


def test_poet_pipeline_e2e_operate_error():
    """Test the pipeline with a function that raises an error."""
    config = POETConfig(domain="test")
    perceive = PerceivePhase(config)
    operate = OperatePhase(config)
    enforce = EnforcePhase(config)

    def error_func(x, y):
        raise ValueError("Test error in operate phase")

    # Step 1: Perceive
    perceive_result = perceive.perceive((2, 3), {})
    assert perceive_result.is_valid

    # Step 2: Operate (error)
    operate_result = operate.operate(error_func, perceive_result.processed_args, perceive_result.processed_kwargs, perceive_result.context)
    assert not operate_result.is_success
    assert any("Operate phase error" in e for e in operate_result.errors)


def test_poet_pipeline_e2e_enforce_error():
    """Test the pipeline with an output type mismatch in Enforce phase."""
    config = POETConfig(domain="test")
    perceive = PerceivePhase(config)
    operate = OperatePhase(config)
    enforce = EnforcePhase(config)

    # Step 1: Perceive
    perceive_result = perceive.perceive((2, 3), {})
    assert perceive_result.is_valid

    # Step 2: Operate
    operate_result = operate.operate(dummy_func, perceive_result.processed_args, perceive_result.processed_kwargs, perceive_result.context)
    assert operate_result.is_success

    # Step 3: Enforce (expecting str, but got int)
    enforce_result = enforce.enforce(operate_result.output, perceive_result.context, expected_type=str)
    assert not enforce_result.is_valid
    assert any("Output type mismatch" in e for e in enforce_result.validation_errors)
