"""Tests for BaseReasoning."""

from typing import List
from unittest.mock import AsyncMock, MagicMock
import pytest

from dxa.core.reasoning.base_reasoning import (
    BaseReasoning,
    ReasoningContext,
    ReasoningConfig
)
from dxa.core.resource import LLMResource

class SimpleReasoning(BaseReasoning):
    """Minimal reasoning implementation for testing."""
    @property
    def steps(self) -> List[str]:
        return ["test"]

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
    return SimpleReasoning(config=config)

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
async def test_basic_reasoning_flow(reasoning, context):
    """Test the basic reasoning flow."""
    result = await reasoning.reason_about({"command": "test"}, context)
    
    assert result.success
    assert result.output == "test response"
    assert result.reasoning_path == ["test"]
    assert len(context.history) > 0

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_error_handling(reasoning, context):
    """Test error handling in reasoning."""
    reasoning.agent_llm.query = AsyncMock(side_effect=ValueError("test error"))
    
    result = await reasoning.reason_about({"command": "test"}, context)
    
    assert not result.success
    assert "test error" in result.output
    assert result.confidence == 0.0

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_context_management(reasoning, context):
    """Test context management during reasoning."""
    await reasoning.reason_about({"command": "test"}, context)
    
    assert len(context.history) > 0
    assert context.workspace == {}  # Should be cleared in _prepare_reasoning

@pytest.mark.asyncio
async def test_llm_required():
    """Test that LLM is required."""
    # pylint: disable=redefined-outer-name
    reasoning = SimpleReasoning()  # No LLM configured
    
    result = await reasoning.reason_about({"command": "test"}, MagicMock())
    assert not result.success
    assert result.insights["error_type"] == "ValueError"
    assert result.output.startswith("No LLM configured")

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_cleanup(reasoning):
    """Test cleanup."""
    await reasoning.cleanup()
    reasoning.agent_llm.cleanup.assert_called_once()