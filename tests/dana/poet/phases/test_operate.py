"""
Tests for POET Operate Phase.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from opendxa.dana.poet.phases.operate import OperatePhase
from opendxa.dana.poet.types import POETConfig


def dummy_func(x, y):
    return x + y


def error_func(x, y):
    raise ValueError("Test error")


def test_operate_phase_basic_execution():
    config = POETConfig()
    phase = OperatePhase(config)
    result = phase.operate(dummy_func, (2, 3), {}, {})
    assert result.is_success
    assert result.output == 5
    assert result.errors == []


def test_operate_phase_error_handling():
    config = POETConfig()
    phase = OperatePhase(config)
    result = phase.operate(error_func, (2, 3), {}, {})
    assert not result.is_success
    assert result.output is None
    assert any("Operate phase error" in e for e in result.errors)


def test_operate_phase_llm_stub():
    config = POETConfig(domain="test", enable_training=True)
    phase = OperatePhase(config)
    result = phase.operate(dummy_func, (1, 2), {}, {})
    # LLM stub returns output unchanged
    assert result.is_success
    assert result.output == 3


def test_operate_phase_pre_post_hooks(monkeypatch):
    config = POETConfig()
    phase = OperatePhase(config)
    pre_called = {}
    post_called = {}

    def pre_hook(args, kwargs, context):
        pre_called["called"] = True

    def post_hook(result):
        post_called["called"] = True

    monkeypatch.setattr(phase, "_pre_operate_hook", pre_hook)
    monkeypatch.setattr(phase, "_post_operate_hook", post_hook)
    result = phase.operate(dummy_func, (4, 5), {}, {})
    assert result.is_success
    assert result.output == 9
    assert pre_called["called"]
    assert post_called["called"]
