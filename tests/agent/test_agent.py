"""Tests for the unified Agent implementation."""

from unittest.mock import AsyncMock
import pytest

from dxa.agent.agent import Agent
from dxa.core.reasoning import (
    DirectReasoning,
    ChainOfThoughtReasoning,
    OODAReasoning,
    ReasoningLevel
)
from dxa.core.resource import BaseResource, LLMResource
from dxa.core.io import BaseIO
from dxa.common.errors import ConfigurationError

@pytest.fixture
def mock_llm():
    """Mock LLM resource."""
    llm = LLMResource(name="test_llm", config={"model_name": "test"})
    llm.query = AsyncMock(return_value={"content": "test response"})
    return llm

# pylint: disable=redefined-outer-name
@pytest.fixture
def agent(mock_llm):
    """Basic agent fixture."""
    return Agent("test_agent", llm=mock_llm)

@pytest.fixture
def mock_resource():
    """Mock resource fixture."""
    return BaseResource(name="test_resource")

@pytest.fixture
def mock_io():
    """Mock IO fixture."""
    return BaseIO()

@pytest.mark.asyncio
async def test_agent_initialization(mock_llm):
    """Test basic agent initialization."""
    agent = Agent("test_agent", llm=mock_llm)
    assert agent.name == "test_agent"
    assert agent.llm == mock_llm
    assert agent.reasoning is None
    assert not agent.resources
    assert not agent.capabilities

@pytest.mark.asyncio
async def test_with_reasoning(agent):
    """Test adding reasoning system."""
    agent.with_reasoning("direct")
    assert isinstance(agent.reasoning, DirectReasoning)
    assert agent.reasoning.agent_llm == agent.llm

@pytest.mark.asyncio
async def test_with_resources(agent, mock_resource):
    """Test adding resources."""
    agent.with_resources({"test": mock_resource})
    assert "test" in agent.resources

@pytest.mark.asyncio
async def test_with_capabilities(agent):
    """Test adding capabilities."""
    capabilities = ["research", "analysis"]
    agent.with_capabilities(capabilities)
    assert agent.capabilities == set(capabilities)

@pytest.mark.asyncio
async def test_with_io(agent, mock_io):
    """Test adding IO handler."""
    agent.with_io(mock_io)
    # pylint: disable=protected-access
    assert agent._io == mock_io

@pytest.mark.asyncio
async def test_run_without_reasoning(agent):
    """Test running without reasoning system."""
    with pytest.raises(ConfigurationError):
        await agent.run("test task")

@pytest.mark.asyncio
async def test_run_with_reasoning(agent):
    """Test successful run with reasoning."""
    agent.with_reasoning("direct")
    result = await agent.run("test task")
    assert result is not None
    assert result["agent_name"] == "test_agent"

@pytest.mark.asyncio
async def test_cleanup(agent, mock_resource, mock_io):
    """Test cleanup of all components."""
    agent.with_resources({"test": mock_resource})\
        .with_io(mock_io)
    
    await agent.cleanup()

@pytest.mark.asyncio
async def test_reasoning_configuration():
    """Test different ways to configure reasoning."""
    agent = Agent("test", llm=mock_llm)
    
    # Test with string name
    agent.with_reasoning("cot")
    assert isinstance(agent.reasoning, ChainOfThoughtReasoning)
    
    # Test with reasoning level
    agent.with_reasoning(ReasoningLevel.OODA)
    assert isinstance(agent.reasoning, OODAReasoning)
    
    # Test invalid strategy
    with pytest.raises(ConfigurationError):
        agent.with_reasoning("invalid")

@pytest.mark.asyncio
async def test_minimal_agent(mock_llm):
    """Test most basic agent functionality."""
    agent = Agent("test", llm=mock_llm)
    agent.with_reasoning(ReasoningLevel.DIRECT)
    
    result = await agent.run("What is 2+2?")
    
    assert result is not None
    assert "agent_name" in result
    assert result["agent_name"] == "test"
  