"""Tests for DirectReasoning."""

from unittest.mock import AsyncMock
import pytest

from dxa.core.reasoning import DirectReasoning, ReasoningContext, ReasoningConfig
from dxa.core.resource import LLMResource

@pytest.fixture
def mock_llm():
    """Mock LLM resource."""
    llm = LLMResource(name="test_llm", config={"model_name": "test"})
    llm.query = AsyncMock(return_value={"content": "test response"})
    llm.cleanup = AsyncMock()
    return llm

@pytest.fixture
# pylint: disable=redefined-outer-name
def reasoning(mock_llm):
    """Test reasoning instance."""
    config = ReasoningConfig(agent_llm=mock_llm)
    return DirectReasoning(config=config)

@pytest.fixture
def context():
    """Test reasoning context."""
    return ReasoningContext(
        objective="test objective",
        resources={},
        workspace={},
        history=[]
    )

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_direct_reasoning_basic(reasoning, context):
    """Test basic direct reasoning execution."""
    result = await reasoning.reason_about({"command": "test"}, context)

    assert result.success  # Not dict access, it's a ReasoningResult object
    assert "test response" in result.output
    assert len(context.history) > 0

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_direct_reasoning_error_handling(reasoning, context):
    """Test error handling in direct reasoning."""
    reasoning.agent_llm.query = AsyncMock(side_effect=ValueError("test error"))
    result = await reasoning.reason_about({"command": "test"}, context)

    assert not result.success
    assert "test error" in result.output
    assert result.confidence == 0.0

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_direct_reasoning_custom_prompt(reasoning, context):
    """Test custom system prompt and temperature."""
    result = await reasoning.reason_about({
        "command": "test",
        "system_prompt": "Custom prompt",
        "temperature": 0.5
    }, context)

    assert result.success
    # Verify prompt was passed correctly
    call_args = reasoning.agent_llm.query.call_args[0][0]
    assert "Custom prompt" in str(call_args)
    assert "0.5" in str(call_args) 