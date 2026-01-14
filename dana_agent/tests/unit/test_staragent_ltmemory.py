"""Tests for STARAgent LTMemory integration."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dana.common.protocols.types import LearningPhase


class TestSTARAgentLTMemoryInit:
    """Tests for STARAgent LTMemory initialization."""

    @patch("dana.core.memory.ltmemory.RLMResource")
    @patch("dana.core.agent.star_agent.LLM")
    def test_staragent_with_ltmemory_path(self, mock_llm_class, mock_rlm_class):
        """STARAgent creates LTMemory when ltmemory_path is provided."""
        from dana.core.agent.star_agent import STARAgent
        from dana.core.memory import LTMemory

        with tempfile.TemporaryDirectory() as tmpdir:
            agent = STARAgent(
                agent_type="test",
                ltmemory_path=tmpdir,
                auto_register=False,
            )
            assert agent._ltmemory is not None
            assert isinstance(agent._ltmemory, LTMemory)
            assert agent._ltmemory.path == Path(tmpdir)

    @patch("dana.core.agent.star_agent.LLM")
    def test_staragent_without_ltmemory_path(self, mock_llm_class):
        """STARAgent does not create LTMemory when ltmemory_path is None."""
        from dana.core.agent.star_agent import STARAgent

        agent = STARAgent(
            agent_type="test",
            ltmemory_path=None,
            auto_register=False,
        )
        assert agent._ltmemory is None


@patch("dana.repositories.repository_factory.DEFAULT_REPOSITORY_FACTORY")
class TestLearnerLTMemoryIntegration:
    """Tests for Learner LTMemory integration."""

    def test_reflect_retentive_stores_memories(self, mock_factory):
        """_reflect_retentive stores memories to LTMemory when available."""
        from dana.core.agent.components.learner import Learner

        # Mock the factory
        mock_factory.create.return_value = MagicMock()

        # Create mock LTMemory
        mock_ltmemory = MagicMock()
        mock_ltmemory.store = MagicMock()

        # Create mock agent with LTMemory
        mock_agent = MagicMock()
        mock_agent._ltmemory = mock_ltmemory
        mock_agent._session_id = "test-session"

        learner = Learner(agent=mock_agent)

        # Call _reflect_retentive with trace data
        trace_data = {
            "caller_message": "Find the auth bug",
            "response": "I found the issue in token.py",
            "tool_calls": [],
            "tool_results": [{"type": "resource", "result": "Token expiry not checked"}],
        }
        result = learner._reflect_retentive(trace_data)

        # Verify memories were stored
        assert result["trace_learning"]["memories_stored"] == 2
        assert mock_ltmemory.store.call_count == 2

    def test_reflect_retentive_without_ltmemory(self, mock_factory):
        """_reflect_retentive works without LTMemory."""
        from dana.core.agent.components.learner import Learner

        # Mock the factory
        mock_factory.create.return_value = MagicMock()

        mock_agent = MagicMock()
        mock_agent._ltmemory = None
        mock_agent._session_id = "test-session"

        learner = Learner(agent=mock_agent)

        trace_data = {
            "caller_message": "Find the auth bug",
            "response": "I found the issue",
            "tool_calls": [],
            "tool_results": [],
        }
        result = learner._reflect_retentive(trace_data)

        # Should complete without error, storing 0 memories
        assert result["trace_learning"]["memories_stored"] == 0

    def test_query_learnings_retentive_phase(self, mock_factory):
        """query_learnings queries LTMemory for RETENTIVE phase."""
        from dana.core.agent.components.learner import Learner

        # Mock the factory
        mock_factory.create.return_value = MagicMock()

        # Create mock LTMemory
        mock_ltmemory = MagicMock()
        mock_ltmemory.query.return_value = "Auth bugs relate to token expiry"

        # Create mock agent with LTMemory
        mock_agent = MagicMock()
        mock_agent._ltmemory = mock_ltmemory
        mock_agent._session_id = "test-session"

        learner = Learner(agent=mock_agent)

        # Query for retentive learnings
        result = learner.query_learnings("auth issues", LearningPhase.RETENTIVE)

        assert result == "Auth bugs relate to token expiry"
        mock_ltmemory.query.assert_called_once_with("auth issues")

    def test_query_learnings_returns_none_for_empty_memory(self, mock_factory):
        """query_learnings returns None when LTMemory has no memories."""
        from dana.core.agent.components.learner import Learner

        # Mock the factory
        mock_factory.create.return_value = MagicMock()

        # Create mock LTMemory that returns "No memories stored yet."
        mock_ltmemory = MagicMock()
        mock_ltmemory.query.return_value = "No memories stored yet."

        mock_agent = MagicMock()
        mock_agent._ltmemory = mock_ltmemory
        mock_agent._session_id = "test-session"

        learner = Learner(agent=mock_agent)

        result = learner.query_learnings("test query", LearningPhase.RETENTIVE)
        assert result is None

    def test_query_learnings_other_phase_returns_none(self, mock_factory):
        """query_learnings returns None for non-RETENTIVE phases."""
        from dana.core.agent.components.learner import Learner

        # Mock the factory
        mock_factory.create.return_value = MagicMock()

        mock_agent = MagicMock()
        mock_agent._ltmemory = MagicMock()
        mock_agent._session_id = "test-session"

        learner = Learner(agent=mock_agent)

        result = learner.query_learnings("test query", LearningPhase.ACQUISITIVE)
        assert result is None


@patch("dana.repositories.repository_factory.DEFAULT_REPOSITORY_FACTORY")
class TestDefaultLearnerLTMemoryIntegration:
    """Tests for DefaultLearner LTMemory integration."""

    def test_reflect_retentive_stores_episode_with_tools(self, mock_factory):
        """DefaultLearner._reflect_retentive stores episode with tool names."""
        from dana.core.agent.components.learner import DefaultLearner

        # Mock repository factory
        mock_factory.create.return_value = MagicMock()

        # Create mock LTMemory
        mock_ltmemory = MagicMock()
        mock_ltmemory.store = MagicMock()

        # Create mock agent with LTMemory
        mock_agent = MagicMock()
        mock_agent._ltmemory = mock_ltmemory
        mock_agent._session_id = "test-session"

        learner = DefaultLearner(agent=mock_agent)

        # Call _reflect_retentive with trace data including tool calls
        trace_data = {
            "caller_message": "Search for files",
            "response": "Found 3 files",
            "tool_calls": [
                {"function": "file_search", "arguments": {"query": "*.py"}},
                {"function": "read_file", "arguments": {"path": "main.py"}},
            ],
            "tool_results": [{"type": "resource", "result": "file1.py"}],
        }
        result = learner._reflect_retentive(trace_data)

        # Verify memories were stored
        assert result["trace_learning"]["memories_stored"] == 2
        assert mock_ltmemory.store.call_count == 2

        # Check that the episode memory includes tool names
        episode_call = mock_ltmemory.store.call_args_list[0]
        episode_memory = episode_call[0][0]
        assert "file_search" in episode_memory["content"]
        assert "read_file" in episode_memory["content"]
        assert episode_memory["type"] == "episode"

    def test_default_learner_query_learnings(self, mock_factory):
        """DefaultLearner.query_learnings queries LTMemory."""
        from dana.core.agent.components.learner import DefaultLearner

        # Mock repository factory
        mock_factory.create.return_value = MagicMock()

        # Create mock LTMemory
        mock_ltmemory = MagicMock()
        mock_ltmemory.query.return_value = "Past knowledge about patterns"

        # Create mock agent with LTMemory
        mock_agent = MagicMock()
        mock_agent._ltmemory = mock_ltmemory
        mock_agent._session_id = "test-session"

        learner = DefaultLearner(agent=mock_agent)

        result = learner.query_learnings("patterns", LearningPhase.RETENTIVE)
        assert result == "Past knowledge about patterns"
        mock_ltmemory.query.assert_called_once_with("patterns")
