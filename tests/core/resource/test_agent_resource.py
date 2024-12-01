import pytest
from unittest.mock import AsyncMock, MagicMock
from dxa.core.resource.agent_resource import (
    AgentResource,
    ResourceError,
    ConfigurationError,
    AgentError
)

class MockAgent:
    """Mock agent for testing."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.initialize = AsyncMock()
        self.cleanup = AsyncMock()
        self.run = AsyncMock(return_value={"result": "success"})

@pytest.fixture
def agent_registry():
    """Fixture providing test agent registry."""
    return {
        "agent1": MockAgent("agent1"),
        "agent2": MockAgent("agent2")
    }

@pytest.fixture
async def agent_resource(agent_registry):
    """Fixture providing a test agent resource instance."""
    resource = AgentResource(name="test_agent_resource", agent_registry=agent_registry)
    yield resource
    await resource.cleanup()

@pytest.mark.asyncio
async def test_agent_initialization(agent_registry):
    """Test agent resource initialization."""
    resource = AgentResource(name="test", agent_registry=agent_registry)
    assert resource.name == "test"
    assert resource.agent_registry == agent_registry

@pytest.mark.asyncio
async def test_agent_initialization_empty_registry():
    """Test initialization with empty registry."""
    with pytest.raises(ConfigurationError):
        AgentResource(name="test", agent_registry={})

@pytest.mark.asyncio
async def test_agent_query(agent_resource):
    """Test agent query functionality."""
    response = await agent_resource.query({
        "agent_id": "agent1",
        "query": {"test": "data"}
    })
    
    assert response["success"] is True
    assert response["response"] == {"result": "success"}
    agent_resource.agent_registry["agent1"].run.assert_called_once_with({"test": "data"})

@pytest.mark.asyncio
async def test_agent_query_invalid_agent(agent_resource):
    """Test query with invalid agent ID."""
    with pytest.raises(ConfigurationError):
        await agent_resource.query({
            "agent_id": "nonexistent_agent",
            "query": {}
        })

@pytest.mark.asyncio
async def test_agent_query_missing_agent_id(agent_resource):
    """Test query with missing agent ID."""
    with pytest.raises(ConfigurationError):
        await agent_resource.query({"query": {}})

@pytest.mark.asyncio
async def test_agent_initialization_error():
    """Test agent initialization error handling."""
    failing_agent = MockAgent("failing_agent")
    failing_agent.initialize.side_effect = AgentError("Initialization failed")
    
    registry = {"failing_agent": failing_agent}
    resource = AgentResource(name="test", agent_registry=registry)
    
    with pytest.raises(ResourceError):
        await resource.initialize()

@pytest.mark.asyncio
async def test_agent_cleanup_error():
    """Test agent cleanup error handling."""
    failing_agent = MockAgent("failing_agent")
    failing_agent.cleanup.side_effect = AgentError("Cleanup failed")
    
    registry = {"failing_agent": failing_agent}
    resource = AgentResource(name="test", agent_registry=registry)
    
    with pytest.raises(ResourceError):
        await resource.cleanup() 