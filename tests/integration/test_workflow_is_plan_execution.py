"""Integration tests for WORKFLOW_IS_PLAN execution strategy."""

import pytest
from dxa.agent import Agent
from dxa.execution import WorkflowStrategy, WorkflowFactory
from dxa.execution import ExecutionContext, Objective

from dxa.agent.resource import LLMResource

class MockLLM(LLMResource):
    """Mock LLM for testing."""
    async def query(self, request: dict) -> dict:
        """Mock LLM query."""
        return {"content": f"Mock response for: {request['prompt']}"}

@pytest.fixture
def agent():
    """Create agent with WORKFLOW_IS_PLAN strategy."""
    # pylint: disable=redefined-outer-name
    agent = (Agent()
                .with_workflow(WorkflowStrategy.WORKFLOW_IS_PLAN)
                .with_llm(MockLLM()))
    # pylint: disable=protected-access
    agent._initialize()  # Initialize runtime
    return agent

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_workflow_is_plan_execution(agent):
    """Test full execution flow with WORKFLOW_IS_PLAN strategy."""
    # Execute simple query
    runtime = agent.runtime
    workflow = WorkflowFactory.create_minimal_workflow("test query")
    await agent.async_run(workflow)
    
    # Verify execution completed
    workflow = runtime.workflow_executor.graph
    assert workflow.get_current_node().node_id == "END"

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_context_propagation(agent):
    """Test context propagation through execution layers."""
    workflow_exec = agent.runtime.workflow_executor
    plan_exec = workflow_exec.plan_executor
    reasoning_exec = plan_exec.reasoning_executor
    
    # Run execution
    workflow = WorkflowFactory.create_minimal_workflow("test query")
    await agent.async_run(workflow)
    
    # Verify context consistency
    assert workflow_exec.graph is not None
    assert plan_exec.graph is not None
    assert reasoning_exec.graph is not None

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_graph_safety(agent):
    """Test graph safety mechanisms across execution."""
    context = ExecutionContext(workflow_llm=agent.workflow_llm,
                               planning_llm=agent.planning_llm,
                               reasoning_llm=agent.reasoning_llm)
    workflow_exec = agent.runtime.workflow_executor
    
    # Execute with minimal context
    try:
        await workflow_exec.execute_workflow(
            # pylint: disable=protected-access
            workflow=workflow_exec.create_graph_from_node(None, None, Objective("test"), context),
            context=context
        )
    except ValueError as e:
        assert str(e) == "No workflow/planning/reasoning LLM configured in context"
    
    # Verify graph-context sync
    assert context.current_workflow is not None
    assert context.current_plan is not None
    assert context.current_reasoning is not None
    assert workflow_exec.graph == context.current_workflow 

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_cursor_progression(agent):
    """Test cursor moves through workflow nodes correctly."""
    runtime = agent.runtime
    workflow_exec = runtime.workflow_executor
    
    workflow = WorkflowFactory.create_minimal_workflow("test query")
    await agent.async_run(workflow)
    workflow = workflow_exec.graph
    
    # Verify cursor moved through all nodes
    assert workflow.get_current_node().node_id == "END"
    # Could also track cursor history 
