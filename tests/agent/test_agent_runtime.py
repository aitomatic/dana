"""Tests for AgentRuntime."""

from unittest.mock import AsyncMock
import pytest

@pytest.fixture
def state_manager():
    """State manager fixture."""
    return StateManager("test_agent")

@pytest.fixture
def runtime(state_manager):
    """Runtime fixture."""
    return AgentRuntime(state_manager)

@pytest.mark.asyncio
async def test_runtime_execution():
    """Test basic runtime execution."""
    state_manager = StateManager("test")
    runtime = AgentRuntime(state_manager)
    
    reasoning_step = AsyncMock(return_value={"task_complete": True})
    pre_execute = AsyncMock()
    post_execute = AsyncMock(return_value={"result": "success"})
    
    result = await runtime.execute(
        task={"objective": "test"},
        reasoning_step=reasoning_step,
        pre_execute=pre_execute,
        post_execute=post_execute
    )
    
    assert result["result"] == "success"
    pre_execute.assert_called_once()
    reasoning_step.assert_called_once()
    post_execute.assert_called_once()

@pytest.mark.asyncio
async def test_runtime_progress_updates():
    """Test progress updates during execution."""
    state_manager = StateManager("test")
    runtime = AgentRuntime(state_manager)
    
    reasoning_step = AsyncMock(return_value={"task_complete": True})
    
    progress_updates = []
    async for progress in runtime.execute_with_progress(
        task={"objective": "test"},
        reasoning_step=reasoning_step
    ):
        progress_updates.append(progress)
    
    assert len(progress_updates) > 0
    assert isinstance(progress_updates[0], AgentProgress)
    assert progress_updates[-1].is_result

@pytest.mark.asyncio
async def test_runtime_cleanup():
    """Test runtime cleanup."""
    state_manager = StateManager("test")
    runtime = AgentRuntime(state_manager)
    
    runtime.iteration_count = 5
    runtime._is_running = True
    
    await runtime.cleanup()
    
    assert runtime.iteration_count == 0
    assert not runtime._is_running
    assert len(state_manager.observations) == 0 