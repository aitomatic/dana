"""Integration tests for default strategy execution."""

import pytest
from dxa.core.agent import Agent
from dxa.core.resource import LLMResource
from dxa.common.graph import NodeType
class MockLLM(LLMResource):
    """Mock LLM for testing."""
    async def query(self, request: dict) -> dict:
        return {"content": f"Mock response for: {request['prompt']}"}

@pytest.fixture
def agent():
    """Create agent with default strategies."""
    # pylint: disable=redefined-outer-name
    agent = Agent().with_llm(MockLLM())
    # pylint: disable=protected-access
    agent._initialize()  # Initialize runtime
    return agent

@pytest.mark.asyncio    
# pylint: disable=redefined-outer-name
async def test_default_execution_flow(agent):
    """Test execution with all default strategies."""
    runtime = agent.runtime
    workflow_exec = runtime.workflow_executor
    plan_exec = workflow_exec.plan_executor
    
    # Execute and verify each layer uses default strategy
    await agent.run("test query")
    
    # Verify plan has single node (DEFAULT creates 1:1 mapping)
    plan = plan_exec.graph
    task_nodes = [n for n in plan.nodes.values() if n.node_type == NodeType.TASK]
    assert len(task_nodes) == 1
    assert task_nodes[0].node_id == "DIRECT_STEP" 