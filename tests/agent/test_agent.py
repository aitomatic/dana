"""Tests for the unified Agent implementation."""

from unittest.mock import AsyncMock
from typing import List, Dict, Any
import pytest

from dxa.agent.agent import Agent
from dxa.core.reasoning import (
    BaseReasoning,
    DirectReasoning,
    ChainOfThoughtReasoning,
    OODAReasoning,
    ReasoningLevel
)
from dxa.core.resource import BaseResource
from dxa.core.io import BaseIO
from dxa.common.errors import ConfigurationError

class MockReasoning(BaseReasoning):
    """Mock reasoning for testing."""
    def __init__(self):
        super().__init__()
        self.reason = AsyncMock(return_value={"result": "success"})
        self.cleanup = AsyncMock()

    @property
    def steps(self) -> List[str]:
        return ["mock_step"]

    def get_initial_step(self) -> str:
        return "mock_step"

    def get_step_prompt(self, step: str, context: Dict[str, Any], query: str, previous_steps: List[Dict[str, Any]]) -> str:
        return "mock prompt"

class MockResource(BaseResource):
    """Mock resource for testing."""
    def __init__(self, name="test_resource"):
        super().__init__(name=name)

class MockIO(BaseIO):
    """Mock IO implementation for testing."""
    pass

@pytest.fixture
def agent():
    """Basic agent fixture."""
    return Agent("test_agent")

@pytest.fixture
def mock_reasoning():
    """Mock reasoning fixture."""
    return MockReasoning()

@pytest.fixture
def mock_resource():
    """Mock resource fixture."""
    return MockResource()

@pytest.fixture
def mock_io():
    """Mock IO fixture."""
    return MockIO()

@pytest.mark.asyncio
async def test_agent_initialization():
    """Test basic agent initialization."""
    # pylint: disable=redefined-outer-name
    agent = Agent("test_agent")
    assert agent.name == "test_agent"
    assert agent.reasoning is None
    assert agent.resources == {}
    assert agent.capabilities == set()

# pylint: disable=redefined-outer-name
@pytest.mark.asyncio
async def test_with_reasoning(agent, mock_reasoning):
    """Test adding reasoning system."""
    agent.with_reasoning(mock_reasoning)
    assert agent.reasoning == mock_reasoning

@pytest.mark.asyncio
async def test_with_resources(agent, mock_resource):
    """Test adding resources."""
    agent.with_resources({"test": mock_resource})
    assert "test" in agent.resources
    assert agent.resources["test"] == mock_resource

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
    assert agent.io == mock_io

@pytest.mark.asyncio
async def test_run_without_reasoning(agent):
    """Test running without reasoning system."""
    with pytest.raises(ConfigurationError):
        await agent.run("test task")

@pytest.mark.asyncio
async def test_run_with_reasoning(agent, mock_reasoning):
    """Test successful run with reasoning."""
    agent.with_reasoning(mock_reasoning)
    result = await agent.run("test task")
    assert result == {"result": "success"}
    mock_reasoning.reason.assert_called_once()

@pytest.mark.asyncio
async def test_cleanup(agent, mock_reasoning, mock_resource, mock_io):
    """Test cleanup of all components."""
    agent.with_reasoning(mock_reasoning)\
        .with_resources({"test": mock_resource})\
        .with_io(mock_io)
    
    await agent.cleanup()
    
    mock_reasoning.cleanup.assert_called_once()
    mock_resource.cleanup.assert_called_once()
    mock_io.cleanup.assert_called_once()

@pytest.mark.asyncio
async def test_pre_execute_adds_context(agent, mock_reasoning):
    """Test that pre_execute adds capabilities and resources to context."""
    agent.with_reasoning(mock_reasoning)\
        .with_capabilities(["test_cap"])\
        .with_resources({"test": mock_resource})
    
    context = {}
    await agent.pre_execute(context)
    
    assert "capabilities" in context
    assert "available_resources" in context
    assert "test_cap" in context["capabilities"]
    assert "test" in context["available_resources"]

@pytest.mark.asyncio
async def test_post_execute_adds_metadata(agent):
    """Test that post_execute adds agent metadata to result."""
    result = {}
    updated = await agent.post_execute(result)
    
    assert "agent_name" in updated
    assert updated["agent_name"] == "test_agent"
    assert "capabilities" in updated 

@pytest.mark.asyncio
async def test_reasoning_configuration():
    """Test different ways to configure reasoning."""
    agent = Agent("test")
    
    # Test with direct instance
    direct = DirectReasoning()
    agent.with_reasoning(direct)
    assert agent.reasoning == direct
    
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
async def test_minimal_agent():
    """Test most basic agent functionality with direct reasoning."""
    agent = Agent("test")
    agent.with_reasoning(ReasoningLevel.DIRECT)
    
    result = await agent.run("What is 2+2?")
    
    assert result is not None
    assert "agent_name" in result
    assert result["agent_name"] == "test"
  