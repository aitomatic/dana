"""Tests for the agent resource implementation."""

from unittest.mock import AsyncMock

import pytest

from dxa.agent.base_agent import BaseAgent
from dxa.common.errors import AgentError, ResourceError, ConfigurationError
from dxa.core.resource.agent_resource import AgentResource

class MockAgent(BaseAgent):
    """Mock agent for testing."""
    def __init__(self, agent_id: str):
        super().__init__(name=agent_id, config={}, mode="test")
        self.agent_id = agent_id
        self.initialize = AsyncMock()
        self.cleanup = AsyncMock()
        self.run = AsyncMock(return_value={"result": "success"})

    def get_agent_system_prompt(self) -> str:
        return "test system prompt"

    def get_agent_user_prompt(self) -> str:
        return "test user prompt"

@pytest.fixture
def agents():
    """Fixture providing test agents."""
    return {
        "agent1": MockAgent("agent1"),
        "agent2": MockAgent("agent2")
    }

@pytest.fixture
def agent_resource(agents):
    """Fixture providing test agent resource."""
    return AgentResource(name="test_resource", agents=agents)

@pytest.mark.asyncio
async def test_initialization(agents):
    """Test agent resource initialization."""
    resource = AgentResource(name="test", agents=agents)
    assert resource.name == "test"
    assert resource.agents == agents

@pytest.mark.asyncio
async def test_initialization_empty_agents():
    """Test initialization with empty agents dict."""
    with pytest.raises(ConfigurationError):
        AgentResource(name="test", agents={})

@pytest.mark.asyncio
async def test_query(agent_resource):
    """Test agent query functionality."""
    response = await agent_resource.query({
        "agent_id": "agent1",
        "query": {"test": "data"}
    })
    
    assert response["success"] is True
    assert response["response"] == {"result": "success"}
    agent_resource.agents["agent1"].run.assert_called_once_with({"test": "data"})

@pytest.mark.asyncio
async def test_query_invalid_agent(agent_resource):
    """Test query with invalid agent ID."""
    with pytest.raises(ConfigurationError):
        await agent_resource.query({
            "agent_id": "nonexistent_agent",
            "query": {}
        })

@pytest.mark.asyncio
async def test_query_missing_agent_id(agent_resource):
    """Test query with missing agent ID."""
    with pytest.raises(ConfigurationError):
        await agent_resource.query({"query": {}})

@pytest.mark.asyncio
async def test_initialization_error():
    """Test agent initialization error handling."""
    failing_agent = MockAgent("failing_agent")
    failing_agent.initialize.side_effect = AgentError("Initialization failed")
    
    resource = AgentResource(name="test", agents={"failing_agent": failing_agent})
    
    with pytest.raises(ResourceError):
        await resource.initialize()

@pytest.mark.asyncio
async def test_cleanup_error():
    """Test agent cleanup error handling."""
    failing_agent = MockAgent("failing_agent")
    failing_agent.cleanup.side_effect = AgentError("Cleanup failed")
    
    resource = AgentResource(name="test", agents={"failing_agent": failing_agent})
    
    with pytest.raises(ResourceError):
        await resource.cleanup() 