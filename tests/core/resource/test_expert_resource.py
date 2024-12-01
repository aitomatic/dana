import pytest
from unittest.mock import AsyncMock, patch
from dxa.core.resource.expert_resource import ExpertResource, ExpertConfig
from dxa.core.capability.domain_expertise import DomainExpertise

@pytest.fixture
def expertise():
    """Fixture providing test domain expertise."""
    return DomainExpertise(
        name="Mathematics",
        capabilities=["algebra", "calculus"],
        keywords=["solve", "equation", "derivative"],
        requirements=["equation"],
        description="Test mathematics expert",
        example_queries=["solve x^2 + 2x + 1 = 0", "find derivative of x^3"]
    )

@pytest.fixture
def expert_config(expertise):
    """Fixture providing test expert configuration."""
    return ExpertConfig(
        api_key="test-api-key",
        model="gpt-4",
        expertise=expertise
    )

@pytest.fixture
async def expert_resource(expert_config):
    """Fixture providing a test expert resource instance."""
    resource = ExpertResource(
        name="test_expert",
        config=expert_config
    )
    yield resource
    await resource.cleanup()

@pytest.mark.asyncio
async def test_expert_initialization(expert_config):
    """Test expert resource initialization."""
    expert = ExpertResource(
        name="test",
        config=expert_config
    )
    assert expert.name == "test"
    assert expert.config == expert_config
    assert "Expert in Mathematics" in expert.description

@pytest.mark.asyncio
async def test_expert_can_handle_request(expert_resource):
    """Test request validation."""
    # Valid request with matching keyword and requirement
    assert expert_resource.can_handle({
        "prompt": "solve this equation: x^2 + 2x + 1 = 0"
    }) is True
    
    # Invalid requests
    assert expert_resource.can_handle({}) is False
    assert expert_resource.can_handle({
        "prompt": "tell me a joke"  # No matching keywords
    }) is False
    assert expert_resource.can_handle({
        "prompt": "solve this problem"  # Missing requirement
    }) is False

@pytest.mark.asyncio
@patch('openai.AsyncOpenAI')
async def test_expert_query(mock_openai, expert_resource):
    """Test expert query functionality."""
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="x = -1 ± 0"))]
    mock_response.usage = AsyncMock(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30
    )
    mock_response.model = "gpt-4"
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client
    
    await expert_resource.initialize()
    
    response = await expert_resource.query({
        "prompt": "solve this equation: x^2 + 2x + 1 = 0"
    })
    
    assert response["success"] is True
    assert "x = -1 ± 0" in response["content"]
    assert response["usage"]["total_tokens"] == 30 