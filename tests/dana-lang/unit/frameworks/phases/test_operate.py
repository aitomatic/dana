"""
Tests for POET Operate Phase.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest

from dana.frameworks.poet.core.types import POETConfig
from dana.frameworks.poet.operate import OperatePhase


def dummy_func(x, y):
    return x + y


def error_func(x, y):
    raise ValueError("Test error")


def test_operate_phase_basic_execution():
    config = POETConfig()
    phase = OperatePhase(config)
    result = phase.operate(dummy_func, (2, 3), {}, {})
    assert result == 5


def test_operate_phase_error_handling():
    config = POETConfig()
    phase = OperatePhase(config)
    with pytest.raises(ValueError, match="Test error"):
        phase.operate(error_func, (2, 3), {}, {})


def test_operate_phase_retry_behavior():
    config = POETConfig(retries=2)
    phase = OperatePhase(config)

    # Test that function executes successfully
    result = phase.operate(dummy_func, (1, 2), {}, {})
    assert result == 3


def test_operate_phase_with_retries():
    config = POETConfig(retries=1)
    phase = OperatePhase(config)

    # Test that function fails after retries
    with pytest.raises(ValueError, match="Test error"):
        phase.operate(error_func, (2, 3), {}, {})
