"""Tests for the LLM resource implementation.

This module contains tests for the LLMResource class, which provides
integration with Large Language Models through standardized interfaces.
"""

from unittest.mock import AsyncMock, patch

import pytest

from dxa.core.resource.llm_resource import LLMResource, LLMError
from dxa.core.resource.config import LLMConfig

@pytest.fixture
def llm_config():
    """Fixture providing test LLM configuration."""
    return LLMConfig(
        name="test_llm",
        description="Test LLM config",
        api_key="test-api-key",
        model="gpt-4",
        system_prompt="You are a test assistant."
    )

# pylint: disable=redefined-outer-name
@pytest.fixture
async def llm_resource(llm_config):
    """Fixture providing a test LLM resource instance."""
    async with LLMResource(
        name=llm_config.name,
        config=llm_config
    ) as resource:
        yield resource

@pytest.mark.asyncio
async def test_llm_initialization(llm_config):
    """Test LLM resource initialization."""
    llm = LLMResource(
        name="test",
        config=llm_config
    )
    assert llm.name == "test"
    assert llm.config == llm_config
    assert llm.config["system_prompt"] == "You are a test assistant."

@pytest.mark.asyncio
async def test_llm_can_handle_request(llm_resource):
    """Test request validation."""
    # Valid request
    assert llm_resource.can_handle({"prompt": "Test query"}) is True
    
    # Invalid requests
    assert llm_resource.can_handle({}) is False
    assert llm_resource.can_handle({"prompt": ""}) is False
    assert llm_resource.can_handle({"prompt": "Test", "max_tokens": 5000}) is False

@pytest.mark.asyncio
@patch('openai.AsyncOpenAI')
async def test_llm_query(mock_openai, llm_resource):
    """Test LLM query functionality."""
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Test response"))]
    mock_response.usage = AsyncMock(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30
    )
    mock_response.model = "gpt-4"
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client
    
    await llm_resource.initialize()
    
    response = await llm_resource.query({
        "prompt": "Test query",
        "temperature": 0.7
    })
    
    assert response["success"] is True
    assert response["content"] == "Test response"
    assert response["usage"]["total_tokens"] == 30
    assert response["model"] == "gpt-4"

@pytest.mark.asyncio
async def test_llm_error_handling(llm_resource):
    """Test LLM error scenarios."""
    with pytest.raises(LLMError):
        await llm_resource.query({})  # Missing prompt
        
    with pytest.raises(LLMError):
        await llm_resource.query({"prompt": ""})  # Empty prompt 