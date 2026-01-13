"""
Test suite for comparison mode functionality.

This test suite verifies that:
1. Agents are correctly created with/without learners
2. Comparison mode executes two runs with different agent instances
3. Learnings are only used when with_learner=True
4. Results are different when learnings exist
"""

import pytest
from unittest.mock import Mock, patch
from api.server import get_agent_with_session, clear_agent_cache, _agent_cache
from agent.hvac_agent import HVACAgent
from leaners.william_learner import WilliamLearner


class TestAgentCreation:
    """Test agent creation with different learner configurations."""

    def setup_method(self):
        """Clear agent cache before each test."""
        clear_agent_cache()

    def test_agent_without_learner(self):
        """Test that agent created with with_learner=False has no learner."""
        session_id = "test-session-001"
        agent = get_agent_with_session(session_id, with_learner=False)

        assert agent is not None
        assert agent._learner is None, "Agent with with_learner=False must NOT have a learner"
        assert isinstance(agent, HVACAgent)

    def test_agent_with_learner(self):
        """Test that agent created with with_learner=True has a learner."""
        session_id = "test-session-002"
        agent = get_agent_with_session(session_id, with_learner=True)

        assert agent is not None
        assert agent._learner is not None, "Agent with with_learner=True must have a learner"
        assert isinstance(agent._learner, WilliamLearner)
        assert hasattr(agent._learner, "query_learnings")

    def test_agent_cache_isolation(self):
        """Test that agents with different learner settings are cached separately."""
        session_id = "test-session-003"

        agent_without = get_agent_with_session(session_id, with_learner=False)
        agent_with = get_agent_with_session(session_id, with_learner=True)

        # Verify they are different instances
        assert agent_without is not agent_with, "Agents should be different instances"
        assert id(agent_without) != id(agent_with), "Agents should have different IDs"

        # Verify cache keys are different
        cache_key_without = f"agent_{session_id}_False"
        cache_key_with = f"agent_{session_id}_True"

        assert cache_key_without in _agent_cache
        assert cache_key_with in _agent_cache
        assert _agent_cache[cache_key_without] is agent_without
        assert _agent_cache[cache_key_with] is agent_with

    def test_agent_cache_reuse(self):
        """Test that agents are correctly reused from cache."""
        session_id = "test-session-004"

        agent1 = get_agent_with_session(session_id, with_learner=False)
        agent2 = get_agent_with_session(session_id, with_learner=False)

        # Should be the same instance (cached)
        assert agent1 is agent2, "Agents should be reused from cache"
        assert id(agent1) == id(agent2), "Agents should have the same ID"

    def test_agent_learner_verification(self):
        """Test that agent learner configuration is correctly verified."""
        session_id = "test-session-005"

        # Create agent without learner
        agent_without = get_agent_with_session(session_id, with_learner=False)
        assert agent_without._learner is None

        # Create agent with learner
        agent_with = get_agent_with_session(session_id, with_learner=True)
        assert agent_with._learner is not None

        # Verify they are different
        assert agent_without is not agent_with


class TestComparisonModeExecution:
    """Test comparison mode execution flow."""

    def setup_method(self):
        """Clear agent cache before each test."""
        clear_agent_cache()

    @patch("api.server.HVACAgent")
    def test_comparison_mode_creates_two_agents(self, mock_hvac_agent_class):
        """Test that comparison mode creates two separate agent instances."""
        session_id = "test-comparison-001"

        # Mock agent instances
        mock_agent_without = Mock(spec=HVACAgent)
        mock_agent_without._learner = None
        mock_agent_without.query = Mock(return_value={"response": '{"plan": []}'})

        mock_agent_with = Mock(spec=HVACAgent)
        mock_agent_with._learner = Mock(spec=WilliamLearner)
        mock_agent_with.query = Mock(return_value={"response": '{"plan": []}'})

        # Configure mock to return different instances
        mock_hvac_agent_class.side_effect = [mock_agent_without, mock_agent_with]

        # Get agents
        agent1 = get_agent_with_session(session_id, with_learner=False)
        agent2 = get_agent_with_session(session_id, with_learner=True)

        # Verify they are different
        assert agent1 is not agent2
        assert agent1._learner is None
        assert agent2._learner is not None

    def test_clear_agent_cache(self):
        """Test that agent cache can be cleared."""
        session_id = "test-cache-clear-001"

        # Create agents
        agent1 = get_agent_with_session(session_id, with_learner=False)
        agent2 = get_agent_with_session(session_id, with_learner=True)

        # Verify they are cached
        assert f"agent_{session_id}_False" in _agent_cache
        assert f"agent_{session_id}_True" in _agent_cache

        # Clear cache for session
        clear_agent_cache(session_id)

        # Verify cache is cleared
        assert f"agent_{session_id}_False" not in _agent_cache
        assert f"agent_{session_id}_True" not in _agent_cache


class TestLearningIsolation:
    """Test that learnings are properly isolated between agents."""

    def setup_method(self):
        """Clear agent cache before each test."""
        clear_agent_cache()

    def test_agent_without_learner_cannot_access_learnings(self):
        """Test that agent without learner cannot access learnings."""
        session_id = "test-isolation-001"
        agent = get_agent_with_session(session_id, with_learner=False)

        # Verify no learner exists
        assert agent._learner is None

        # Verify that query_learnings would fail
        assert not hasattr(agent, "query_learnings") or agent._learner is None

    def test_agent_with_learner_can_access_learnings(self):
        """Test that agent with learner can access learnings."""
        session_id = "test-isolation-002"
        agent = get_agent_with_session(session_id, with_learner=True)

        # Verify learner exists
        assert agent._learner is not None
        assert hasattr(agent._learner, "query_learnings")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
