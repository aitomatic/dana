"""Tests for Agent class."""

from unittest.mock import AsyncMock
import pytest
from dxa.agent import Agent, AgentFactory
from dxa.core.resource import LLMResource
from dxa.core.reasoning import DirectReasoning, ReasoningResult

@pytest.fixture
def mock_llm():
    """Create mock LLM resource."""
    llm = LLMResource(name="test_llm", config={"model_name": "gpt-4"})
    llm.query = AsyncMock(return_value={"content": "test response"})
    return llm

# pylint: disable=redefined-outer-name
@pytest.fixture
def basic_agent(mock_llm):
    """Create basic agent for testing."""
    return Agent("test")\
        .with_reasoning("direct")\
        .with_resources({
            "llm": mock_llm
        })

@pytest.mark.asyncio
async def test_agent_execution(basic_agent):
    """Test basic agent execution."""
    result = await basic_agent.run("Test task")
    assert isinstance(result, ReasoningResult)
    assert result.content == "test response"

@pytest.mark.asyncio
async def test_agent_context_management(mock_llm):
    """Test agent context management."""
    async with Agent("test") as agent:
        agent.with_reasoning("direct")\
            .with_resources({"llm": mock_llm})

        result = await agent.run("Test task")
        assert isinstance(result, ReasoningResult)
        assert mock_llm.query.called

@pytest.mark.asyncio
async def test_agent_factory(mock_llm):
    """Test agent creation through factory."""
    agent = AgentFactory.from_config({
        "name": "test",
        "reasoning": "cot",
        "resources": {
            "llm": mock_llm
        }
    })
    assert agent.name == "test"
    assert agent.reasoning is not None
    
    result = await agent.run("Test factory agent")
    assert isinstance(result, ReasoningResult)
    assert mock_llm.query.called
  