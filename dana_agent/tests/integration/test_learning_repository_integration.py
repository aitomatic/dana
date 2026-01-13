"""
Integration tests for Learning Repository with WilliamLearner.

Tests the full save/load cycle with LocalLearningRepository.
"""

from datetime import datetime
import shutil
import tempfile
from unittest.mock import Mock

from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
from dana.repositories import LocalLearningRepository


class MockAgentForIntegration(BaseAgent):
    """Mock agent for integration testing."""

    def __init__(self, codec=None, storage_config=None, **kwargs):
        super().__init__(agent_type="test_agent", agent_id="test-agent-123", **kwargs)
        if codec is None:
            self._codec = Mock()
            self._codec.__qualname__ = "TestCodec"
        else:
            self._codec = codec
        if storage_config is None:
            self._storage_config = FileStorageConfig(workspace_folder=tempfile.mkdtemp())
        else:
            self._storage_config = storage_config
        self._session_id = "test-session-001"


class TestLearningRepositoryIntegration:
    """Integration tests for Learning Repository."""

    def test_save_and_load_acquisitive_loops(self):
        """Test saving and loading acquisitive loops."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            repository = LocalLearningRepository(config, agent)

            session_id = agent._session_id

            # Save multiple loops
            for i in range(3):
                loop_data = {
                    "loop_id": f"test-loop-{i}",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "learning_note": f"Learning note {i}",
                }
                repository.save_acquisitive_loop(session_id, loop_data, f"test-loop-{i}", datetime.now())

            # Load back
            learning_notes = repository.load_acquisitive_loops(session_id)

            assert len(learning_notes) == 3
            assert "Learning note 0" in learning_notes
            assert "Learning note 1" in learning_notes
            assert "Learning note 2" in learning_notes
        finally:
            shutil.rmtree(temp_dir)

    def test_save_and_load_episodic_learning(self):
        """Test saving and loading episodic learning."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            repository = LocalLearningRepository(config, agent)

            session_id = agent._session_id
            content = "Test episodic learning content"

            # Save
            repository.save_episodic_learning(session_id, content)

            # Load back
            loaded_content = repository.load_episodic_learning(session_id)

            assert loaded_content == content
        finally:
            shutil.rmtree(temp_dir)

    def test_save_and_load_feedback(self):
        """Test saving and loading feedback."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            repository = LocalLearningRepository(config, agent)

            session_id = agent._session_id
            content = "Test feedback content"

            # Save
            repository.save_feedback(session_id, content)

            # Load back
            loaded_content = repository.load_feedback(session_id)

            assert loaded_content == content
        finally:
            shutil.rmtree(temp_dir)

    def test_full_learning_cycle(self):
        """Test full learning cycle: acquisitive, episodic, and feedback."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgentForIntegration(storage_config=config)
            repository = LocalLearningRepository(config, agent)

            session_id = agent._session_id

            # Save acquisitive loop
            loop_data = {
                "loop_id": "test-loop-1",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "learning_note": "Test learning note",
            }
            repository.save_acquisitive_loop(session_id, loop_data, "test-loop-1", datetime.now())

            # Save episodic learning
            episodic_content = "Test episodic learning"
            repository.save_episodic_learning(session_id, episodic_content)

            # Save feedback
            feedback_content = "Test feedback"
            repository.save_feedback(session_id, feedback_content)

            # Load all back
            learning_notes = repository.load_acquisitive_loops(session_id)
            loaded_episodic = repository.load_episodic_learning(session_id)
            loaded_feedback = repository.load_feedback(session_id)

            assert len(learning_notes) == 1
            assert learning_notes[0] == "Test learning note"
            assert loaded_episodic == episodic_content
            assert loaded_feedback == feedback_content
        finally:
            shutil.rmtree(temp_dir)
