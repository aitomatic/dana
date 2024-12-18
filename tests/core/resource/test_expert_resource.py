"""Tests for the expert resource implementation."""

from unittest.mock import AsyncMock, patch
import pytest

from dxa.core.resource.expert_resource import ExpertResource, ExpertConfig
from dxa.core.capability.domain_expertise import DomainExpertise
from dxa.core.resource.llm_resource import LLMConfig

@pytest.fixture
def domain_expertise():
    """Fixture providing test domain expertise."""
    return DomainExpertise(
        name="Mathematics",
        capabilities=["algebra", "calculus"],
        keywords=["solve", "equation", "derivative"],
        description="Test mathematics expert",
        requirements=["equation"],
        example_queries=["solve x^2 + 2x + 1 = 0"]
    )

@pytest.fixture
def llm_config():
    """Fixture providing test LLM configuration."""
    return LLMConfig(
        name="test_llm",
        model_name="gpt-4",
        api_key="test-api-key"
    )

# pylint: disable=redefined-outer-name
@pytest.fixture
def expert_config(domain_expertise, llm_config):
    """Fixture providing test expert configuration."""
    return ExpertConfig(
        name="test_expert",
        description="Test expert config",
        expertise=domain_expertise,
        llm_config=llm_config,
        confidence_threshold=0.7
    )

@pytest.mark.asyncio
async def test_expert_initialization(expert_config):
    """Test expert resource initialization."""
    expert = ExpertResource(
        name="test",
        config=expert_config
    )
    assert expert.name == "test"
    assert expert.config == expert_config
    assert not expert.is_available

@pytest.mark.asyncio
async def test_expert_initialization_validation():
    """Test expert initialization validation."""
    with pytest.raises(ValueError, match="requires expertise configuration"):
        ExpertResource(name="test", config=ExpertConfig(name="test"))
        
    with pytest.raises(ValueError, match="requires LLM configuration"):
        ExpertResource(
            name="test",
            config=ExpertConfig(
                name="test",
                expertise=DomainExpertise(
                    name="test",
                    capabilities=[],
                    keywords=[],
                    description="Test domain",
                    requirements=[],
                    example_queries=[]
                )
            )
        )

@pytest.mark.asyncio
async def test_expert_lifecycle(expert_config):
    """Test expert resource lifecycle."""
    expert = ExpertResource(name="test", config=expert_config)
    
    assert not expert.is_available
    await expert.initialize()
    assert expert.is_available
    await expert.cleanup()
    assert not expert.is_available

@pytest.mark.asyncio
@patch('dxa.core.resource.llm_resource.AsyncOpenAI')
async def test_expert_query(mock_openai, expert_config):
    """Test expert query functionality."""
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="x = -1"))]
    mock_response.usage = AsyncMock(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30
    )
    mock_response.model = "gpt-4"
    
    # Setup mock client
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client
    
    expert = ExpertResource(name="test", config=expert_config)
    await expert.initialize()
    
    try:
        response = await expert.query({
            "prompt": "solve equation: x^2 + 2x + 1 = 0"
        })
        
        assert response.content == "x = -1"
        assert response.usage["total_tokens"] == 30
        assert response.model == "gpt-4"
        
    finally:
        await expert.cleanup()

@pytest.mark.asyncio
async def test_expert_can_handle(expert_config):
    """Test request validation."""
    expert = ExpertResource(name="test", config=expert_config)
    
    # Valid request with matching keyword
    assert expert.can_handle({
        "prompt": "solve this equation: x^2 + 2x + 1 = 0"
    }) is True

    # Invalid requests
    assert expert.can_handle({}) is False
    assert expert.can_handle({
        "prompt": "tell me a joke"  # No matching keywords
    }) is False