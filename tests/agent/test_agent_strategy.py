"""Test agent strategy configuration."""

from opendxa import Agent, PlanStrategy

def test_default_strategies():
    """Test default strategy values."""
    agent = Agent()
    assert agent.planning_strategy == PlanStrategy.DEFAULT 