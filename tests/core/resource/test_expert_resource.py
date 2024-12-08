"""Tests for the expert resource implementation.

This module contains tests for the ExpertResource class, which combines
domain expertise with LLM capabilities to provide specialized agents.
"""

from unittest.mock import AsyncMock, patch

import pytest

from dxa.core.resource.expert_resource import ExpertResource, ExpertConfig
from dxa.core.capability.domain_expertise import DomainExpertise

@pytest.fixture
def domain_expertise():
    """Fixture providing test domain expertise."""
    return DomainExpertise(
        name="Mathematics",
        capabilities=["algebra", "calculus"],
        keywords=["solve", "equation", "derivative"],
        requirements=["equation"],
        description="Test mathematics expert",
        example_queries=["solve x^2 + 2x + 1 = 0", "find derivative of x^3"]
    )

# pylint: disable=redefined-outer-name
@pytest.fixture
def expert_config(domain_expertise):
    """Fixture providing test expert configuration."""
    # pylint: disable=unexpected-keyword-arg
    return ExpertConfig(
        name="test_expert",
        description="Test expert config",
        expertise=domain_expertise,
        api_key="test-api-key",
        model="gpt-4"
    )

@pytest.fixture
async def expert_resource(expert_config):
    """Fixture providing a test expert resource instance."""
    # pylint: disable=unexpected-keyword-arg
    async with ExpertResource(
        name=expert_config.name,
        config=expert_config
    ) as resource:
        yield resource

@pytest.mark.asyncio
async def test_expert_initialization(expert_config):
    """Test expert resource initialization."""
    # pylint: disable=unexpected-keyword-arg
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
@patch('dxa.common.base_llm.AsyncOpenAI')
@patch('dxa.core.resource.llm_resource.AsyncOpenAI')
async def test_expert_query(mock_openai_llm, mock_openai_base, mock_openai, expert_config):
    """Test expert query functionality."""
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="x = -1 ± 0"))]
    mock_response.usage = AsyncMock(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30
    )
    mock_response.model = "gpt-4"
    
    # Setup mock client
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_llm.return_value = mock_client
    mock_openai_base.return_value = mock_client
    mock_openai.return_value = mock_client
    
    # Create and initialize resource after mock setup
    resource = ExpertResource(name="test_expert", config=expert_config)
    await resource.initialize()
    
    try:
        response = await resource.query({
            "prompt": "solve this equation: x^2 + 2x + 1 = 0"
        })
        
        assert response.content == "x = -1 ± 0"
        assert response.usage["total_tokens"] == 30
        assert response.model == "gpt-4"
        
        # Verify mock was called correctly
        mock_client.chat.completions.create.assert_called_once()
    finally:
        await resource.cleanup() 