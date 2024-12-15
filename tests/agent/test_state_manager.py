"""Tests for StateManager."""

import pytest

from dxa.agent.agent_runtime import StateManager, AgentState, Observation, Message

@pytest.fixture
def state_manager():
    """State manager fixture."""
    return StateManager("test_agent")

def test_state_manager_initialization(state_manager):
    """Test state manager initialization."""
    assert state_manager.agent_name == "test_agent"
    assert isinstance(state_manager.state, AgentState)
    assert state_manager.state.status == "initializing"

def test_update_state(state_manager):
    """Test state updates."""
    state_manager.update_state("running", {"key": "value"})
    assert state_manager.state.status == "running"
    assert state_manager.state.metadata == {"key": "value"}

def test_add_observation(state_manager):
    """Test adding observations."""
    state_manager.add_observation("test data", "test_source")
    assert len(state_manager.observations) == 1
    assert isinstance(state_manager.observations[0], Observation)
    assert state_manager.observations[0].content == "test data"

def test_add_message(state_manager):
    """Test adding messages."""
    state_manager.add_message("test message", "sender", "receiver")
    assert len(state_manager.messages) == 1
    assert isinstance(state_manager.messages[0], Message)
    assert state_manager.messages[0].content == "test message"

def test_get_recent_observations(state_manager):
    """Test retrieving recent observations."""
    for i in range(10):
        state_manager.add_observation(f"obs_{i}", "source")
    
    recent = state_manager.get_recent_observations(5)
    assert len(recent) == 5
    assert recent[-1].content == "obs_9"

def test_clear_history(state_manager):
    """Test clearing history."""
    state_manager.add_observation("test", "source")
    state_manager.add_message("test", "sender", "receiver")
    state_manager.working_memory["key"] = "value"
    
    state_manager.clear_history()
    
    assert len(state_manager.observations) == 0
    assert len(state_manager.messages) == 0
    assert len(state_manager.working_memory) == 0 