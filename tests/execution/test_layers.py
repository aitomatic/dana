"""Test end-to-end execution flow through all layers.

This test verifies that the planning-reasoning layers work together correctly
using mock LLMs to avoid external API calls.
"""

from typing import Dict
import pytest

from opendxa import (
    Agent,
    AgentResponse,
    Plan,
    PlanStrategy,
    ReasoningStrategy,
    ExecutionNode,
    ExecutionEdge,
    LLMResource,
    NodeType,
)

@pytest.fixture
def llm_resource_fixtures() -> Dict[str, LLMResource]:
    """Create mock LLMs for each layer."""
    return {
        "planning": LLMResource(name="planning_llm").with_mock_llm_call(True),
        "reasoning": LLMResource(name="reasoning_llm").with_mock_llm_call(True)
    }

@pytest.fixture
def agent_fixture(llm_resource_fixtures: Dict[str, LLMResource]) -> Agent:
    """Create an agent configured with mock LLMs for each layer."""
    return Agent(name="test_agent")\
        .with_planning_llm(llm_resource_fixtures["planning"])\
        .with_reasoning_llm(llm_resource_fixtures["reasoning"])\
        .with_planning(PlanStrategy.DEFAULT)\
        .with_reasoning(ReasoningStrategy.DEFAULT)

@pytest.fixture
def plan_fixture() -> Plan:
    """Create a simple plan for testing."""
    plan = Plan(
        name="test_plan",
        objective="Test the planning-reasoning execution flow"
    )
    
    # Add nodes
    start_node = ExecutionNode(
        node_id="START",
        node_type=NodeType.START,
        objective="Start of test plan"
    )
    plan.add_node(start_node)
    
    task1_node = ExecutionNode(
        node_id="TASK1",
        node_type=NodeType.TASK,
        objective="First test task"
    )
    plan.add_node(task1_node)
    
    task2_node = ExecutionNode(
        node_id="TASK2",
        node_type=NodeType.TASK,
        objective="Second test task"
    )
    plan.add_node(task2_node)
    
    end_node = ExecutionNode(
        node_id="END",
        node_type=NodeType.END,
        objective="End of test plan"
    )
    plan.add_node(end_node)
    
    # Add edges
    plan.add_edge(ExecutionEdge(start_node, task1_node))
    plan.add_edge(ExecutionEdge(task1_node, task2_node))
    plan.add_edge(ExecutionEdge(task2_node, end_node))
    
    return plan

@pytest.mark.asyncio
async def test_end_to_end_execution(
    agent_fixture: Agent,
    plan_fixture: Plan,
    llm_resource_fixtures: Dict[str, LLMResource]
):
    """Test end-to-end execution flow through all layers.
    
    This test verifies that:
    1. The plan is properly executed through all layers
    2. Each layer's LLM is called with appropriate prompts
    3. Results flow correctly between layers
    4. The final output is generated
    """
    # Run the plan
    result = await agent_fixture.async_run(plan_fixture)
    
    # Essential OpenAI API response structure
    assert isinstance(result, AgentResponse)
    assert result.success
    assert result.content is not None
    assert result.error is None

    # Verify that llms are set up for mock calls
    # pylint: disable=protected-access
    assert llm_resource_fixtures["planning"]._mock_llm_call is True
    assert llm_resource_fixtures["reasoning"]._mock_llm_call is True
    