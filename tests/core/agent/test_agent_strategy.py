"""Test agent strategy configuration."""

from dxa.core.agent import Agent
from dxa.core.execution import WorkflowStrategy
from dxa.core.execution import PlanningStrategy

def test_workflow_is_plan_strategy_propagation():
    """Test that WORKFLOW_IS_PLAN strategy sets both workflow and planning."""
    agent = Agent().with_workflow(WorkflowStrategy.WORKFLOW_IS_PLAN)
    
    assert agent.workflow_strategy == WorkflowStrategy.WORKFLOW_IS_PLAN
    assert agent.planning_strategy == PlanningStrategy.WORKFLOW_IS_PLAN

def test_planning_is_workflow_strategy_propagation():
    """Test that WORKFLOW_IS_PLAN planning strategy sets workflow strategy."""
    agent = Agent().with_planning(PlanningStrategy.WORKFLOW_IS_PLAN)
    
    assert agent.planning_strategy == PlanningStrategy.WORKFLOW_IS_PLAN
    assert agent.workflow_strategy == WorkflowStrategy.WORKFLOW_IS_PLAN 

def test_default_strategies():
    """Test default strategy values."""
    agent = Agent()
    assert agent.workflow_strategy == WorkflowStrategy.DEFAULT
    assert agent.planning_strategy == PlanningStrategy.DEFAULT 