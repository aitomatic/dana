"""Test plan workflow copy strategy."""

import pytest
from dxa.execution import WorkflowFactory
from dxa.execution import PlanExecutor, PlanningStrategy
from dxa.execution import ReasoningExecutor, ExecutionContext

@pytest.fixture
def workflow():
    """Workflow fixture."""
    return WorkflowFactory.create_minimal_workflow("test workflow")

@pytest.fixture
def plan_executor():
    """Plan executor fixture."""
    reasoning_executor = ReasoningExecutor()
    return PlanExecutor(
        reasoning_executor=reasoning_executor,
        strategy=PlanningStrategy.WORKFLOW_IS_PLAN
    )

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_workflow_copy_creation(workflow, plan_executor):
    """Test creation of plan as exact copy of workflow."""
    # pylint: disable=protected-access
    plan = plan_executor._create_follow_workflow_plan(workflow, workflow.objective)
    
    # Verify structure copying
    assert len(plan.nodes) == len(workflow.nodes)
    assert len(plan.edges) == len(workflow.edges)
    
    # Verify node preservation
    for node_id in workflow.nodes:
        assert node_id in plan.nodes
        assert plan.nodes[node_id].node_type == workflow.nodes[node_id].node_type 

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_plan_execution_updates_workflow_cursor(workflow, plan_executor):
    """Test that plan execution updates workflow cursor."""
    # pylint: disable=protected-access
    plan = plan_executor._create_follow_workflow_plan(workflow, workflow.objective)
    context = ExecutionContext(current_workflow=workflow, current_plan=plan)

    try:
        await plan_executor.execute_node(plan.nodes["PERFORM_TASK"], context, None, None)
    except ValueError as e:
        assert str(e) == "No reasoning LLM configured in context"
    
    assert workflow.get_current_node().node_id == "PERFORM_TASK" 
