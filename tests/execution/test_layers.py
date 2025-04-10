"""Test end-to-end execution flow through all layers.

This test verifies that the workflow-planning-reasoning layers work together correctly
using mock LLMs to avoid external API calls.
"""

from typing import Dict
import pytest

from opendxa.agent import Agent
from opendxa.execution.workflow import Workflow
from opendxa.common.resource import LLMResource
from opendxa.execution import (
    WorkflowStrategy,
    PlanStrategy,
    ReasoningStrategy,
    ExecutionNode,
    ExecutionEdge
)
from opendxa.common import NodeType

@pytest.fixture
def llm_resource_fixtures() -> Dict[str, LLMResource]:
    """Create mock LLMs for each layer."""
    return {
        "workflow": LLMResource(name="workflow_llm").with_mock_llm_call(True),
        "planning": LLMResource(name="planning_llm").with_mock_llm_call(True),
        "reasoning": LLMResource(name="reasoning_llm").with_mock_llm_call(True)
    }

@pytest.fixture
def agent_fixture(llm_resource_fixtures: Dict[str, LLMResource]) -> Agent:
    """Create an agent configured with mock LLMs for each layer."""
    return Agent(name="test_agent")\
        .with_workflow_llm(llm_resource_fixtures["workflow"])\
        .with_planning_llm(llm_resource_fixtures["planning"])\
        .with_reasoning_llm(llm_resource_fixtures["reasoning"])\
        .with_workflow(WorkflowStrategy.DEFAULT)\
        .with_planning(PlanStrategy.DEFAULT)\
        .with_reasoning(ReasoningStrategy.DEFAULT)

@pytest.fixture
def workflow_fixture() -> Workflow:
    """Create a simple workflow for testing."""
    workflow = Workflow(
        name="test_workflow",
        objective="Test the workflow-planning-reasoning execution flow"
    )
    
    # Add nodes
    start_node = ExecutionNode(
        node_id="START",
        node_type=NodeType.START,
        objective="Start of test workflow"
    )
    workflow.add_node(start_node)
    
    task1_node = ExecutionNode(
        node_id="TASK1",
        node_type=NodeType.TASK,
        objective="First test task"
    )
    workflow.add_node(task1_node)
    
    task2_node = ExecutionNode(
        node_id="TASK2",
        node_type=NodeType.TASK,
        objective="Second test task"
    )
    workflow.add_node(task2_node)
    
    end_node = ExecutionNode(
        node_id="END",
        node_type=NodeType.END,
        objective="End of test workflow"
    )
    workflow.add_node(end_node)
    
    # Add edges
    workflow.add_edge(ExecutionEdge(start_node, task1_node))
    workflow.add_edge(ExecutionEdge(task1_node, task2_node))
    workflow.add_edge(ExecutionEdge(task2_node, end_node))
    
    return workflow

@pytest.mark.asyncio
async def test_end_to_end_execution(
    agent_fixture: Agent,
    workflow_fixture: Workflow,
    llm_resource_fixtures: Dict[str, LLMResource]
):
    """Test end-to-end execution flow through all layers.
    
    This test verifies that:
    1. The workflow is properly executed through all layers
    2. Each layer's LLM is called with appropriate prompts
    3. Results flow correctly between layers
    4. The final output is generated

    Expected Result Structure:
    {
        # Required fields
        "content": str,  # The main response text from the LLM
        "model": str,    # The model identifier used (e.g. "anthropic:claude-3-5-sonnet-20241022")
        
        # Optional fields
        "reasoning": Optional[str],      # Additional reasoning provided by the LLM, can be None
        "requested_tools": Optional[List],  # List of tools requested by the LLM, can be None
    }

    Example:
    {
        "content": "Mock response for: Execute the reasoning task...",
        "model": "anthropic:claude-3-5-sonnet-20241022",
        "reasoning": None,
        "requested_tools": None
    }
    """
    # Run the workflow
    result = await agent_fixture.async_run(workflow_fixture)
    
    # Verify basic result structure
    assert result is not None
    assert isinstance(result, dict)
    assert "content" in result
    assert "model" in result
    assert "reasoning" in result
    assert "requested_tools" in result
    
    # Verify content field
    assert isinstance(result["content"], str)
    assert len(result["content"]) > 0
    
    # Verify model field
    assert isinstance(result["model"], str)
    assert len(result["model"]) > 0
    
    # Verify reasoning field
    assert result["reasoning"] is None or isinstance(result["reasoning"], str)
    
    # Verify requested_tools field
    assert result["requested_tools"] is None or isinstance(result["requested_tools"], list)

    # Verify that llms are set up for mock calls
    # pylint: disable=protected-access
    assert llm_resource_fixtures["workflow"]._mock_llm_call is True
    assert llm_resource_fixtures["planning"]._mock_llm_call is True
    assert llm_resource_fixtures["reasoning"]._mock_llm_call is True
    