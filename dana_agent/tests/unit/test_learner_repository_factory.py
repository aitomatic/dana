"""
Unit tests for Learner classes using RepositoryFactory.

Tests that Learner classes use RepositoryFactory to create repositories.
"""

import shutil
import tempfile
from unittest.mock import Mock

from dana.config.storage_config import FileStorageConfig
from dana.core.agent.base_agent import BaseAgent
from dana.core.agent.components.learner import DefaultLearner, Learner
from dana.repositories.local_file_repository import LocalLearningRepository
from dana.repositories.repository_factory import RepositoryFactory, RepositoryType


class MockSTARAgent(BaseAgent):
    """Mock STARAgent for testing."""

    def __init__(self, **kwargs):
        super().__init__(agent_type="test_agent", agent_id="test-agent-123", **kwargs)
        self._codec = Mock()
        self._codec.__qualname__ = "TestCodec"
        self._session_id = "test-session-001"
        self._event_log = None


class TestLearnerRepositoryFactory:
    """Test Learner classes use RepositoryFactory."""

    def test_learner_uses_factory_to_create_repository(self):
        """Test that Learner uses RepositoryFactory to create repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockSTARAgent()

            # Mock the factory
            mock_factory = Mock(spec=RepositoryFactory)
            mock_repository = Mock(spec=LocalLearningRepository)
            mock_factory.create.return_value = mock_repository

            learner = Learner(agent, repository_factory=mock_factory)

            # Verify factory.create was called with correct parameters
            mock_factory.create.assert_called_once_with(RepositoryType.LEARNING, agent=agent)

            # Verify repository is set
            assert learner._repository == mock_repository
        finally:
            shutil.rmtree(temp_dir)

    def test_learner_uses_default_factory_when_not_provided(self):
        """Test that Learner uses DEFAULT_REPOSITORY_FACTORY when not provided."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockSTARAgent()

            learner = Learner(agent)

            # Verify repository is created (should be LocalLearningRepository)
            assert learner._repository is not None
            assert isinstance(learner._repository, LocalLearningRepository)
            assert learner._repository._agent == agent
        finally:
            shutil.rmtree(temp_dir)

    def test_default_learner_uses_factory_to_create_repository(self):
        """Test that DefaultLearner uses RepositoryFactory to create repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockSTARAgent()

            # Mock the factory
            mock_factory = Mock(spec=RepositoryFactory)
            mock_repository = Mock(spec=LocalLearningRepository)
            mock_factory.create.return_value = mock_repository

            learner = DefaultLearner(agent, repository_factory=mock_factory)

            # Verify factory.create was called with correct parameters
            mock_factory.create.assert_called_once_with(RepositoryType.LEARNING, agent=agent)

            # Verify repository is set
            assert learner._repository == mock_repository
        finally:
            shutil.rmtree(temp_dir)

    def test_default_learner_uses_default_factory_when_not_provided(self):
        """Test that DefaultLearner uses DEFAULT_REPOSITORY_FACTORY when not provided."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockSTARAgent()

            learner = DefaultLearner(agent)

            # Verify repository is created (should be LocalLearningRepository)
            assert learner._repository is not None
            assert isinstance(learner._repository, LocalLearningRepository)
            assert learner._repository._agent == agent
        finally:
            shutil.rmtree(temp_dir)

    def test_learner_load_acquisitive_uses_repository(self):
        """Test that Learner._load_acquisitive uses repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockSTARAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalLearningRepository(config, agent)

            learner = Learner(agent)
            learner._repository = repository

            # Mock repository method
            repository.load_acquisitive_loops = Mock(return_value=["learning1", "learning2"])

            result = learner._load_acquisitive()

            # Verify repository method was called
            repository.load_acquisitive_loops.assert_called_once_with(agent._session_id)
            assert result == ["learning1", "learning2"]
        finally:
            shutil.rmtree(temp_dir)

    def test_learner_load_episodic_uses_repository(self):
        """Test that Learner._load_episodic uses repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockSTARAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalLearningRepository(config, agent)

            learner = Learner(agent)
            learner._repository = repository

            # Mock repository method
            repository.load_episodic_learning = Mock(return_value="episodic learning content")

            result = learner._load_episodic()

            # Verify repository method was called
            repository.load_episodic_learning.assert_called_once_with(agent._session_id)
            assert result == "episodic learning content"
        finally:
            shutil.rmtree(temp_dir)

    def test_learner_save_feedback_uses_repository(self):
        """Test that Learner.save_feedback uses repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockSTARAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalLearningRepository(config, agent)

            learner = Learner(agent)
            learner._repository = repository

            # Mock repository method
            repository.save_feedback = Mock()

            learner.save_feedback("test feedback")

            # Verify repository method was called
            repository.save_feedback.assert_called_once_with(agent._session_id, "test feedback")
        finally:
            shutil.rmtree(temp_dir)

    def test_learner_load_feedback_uses_repository(self):
        """Test that Learner._load_feedback uses repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockSTARAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalLearningRepository(config, agent)

            learner = Learner(agent)
            learner._repository = repository

            # Mock repository method
            repository.load_feedback = Mock(return_value="feedback content")

            result = learner._load_feedback()

            # Verify repository method was called
            repository.load_feedback.assert_called_once_with(agent._session_id)
            assert result == "feedback content"
        finally:
            shutil.rmtree(temp_dir)
