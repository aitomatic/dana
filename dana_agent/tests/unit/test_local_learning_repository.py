"""
Unit tests for LocalLearningRepository.

Tests the local file-based learning repository with agent binding.
"""

from datetime import datetime
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import MagicMock, Mock

import pytest


# Mock the problematic import before any dana imports
sys.modules["dana.core.knowledge.prompts.agent_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.resource_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.workflow_prompt_engineer"] = MagicMock()

# Now import normally
from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
from dana.repositories import LocalLearningRepository


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    def __init__(self, codec=None, storage_config=None, **kwargs):
        super().__init__(agent_type="test_agent", agent_id="test-agent-123", **kwargs)
        # Mock codec
        if codec is None:
            self._codec = Mock()
            self._codec.__qualname__ = "TestCodec"
        else:
            self._codec = codec
        # Mock storage_config
        if storage_config is None:
            self._storage_config = FileStorageConfig(workspace_folder=tempfile.mkdtemp())
        else:
            self._storage_config = storage_config


class TestLocalLearningRepositoryInitialization:
    """Test LocalLearningRepository initialization."""

    def test_initialization_extracts_codec_from_agent(self):
        """Test initialization extracts codec from agent."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            assert repository._codec is not None
            assert repository._codec.__qualname__ == "TestCodec"
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_extracts_storage_config_from_agent(self):
        """Test initialization extracts storage_config from agent."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            assert repository.storage_config == config
            assert repository._workspace_folder == Path(temp_dir)
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_creates_default_storage_config_if_missing(self):
        """Test initialization creates default storage_config if agent doesn't have it."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            # Remove storage_config
            delattr(agent, "_storage_config")
            repository = LocalLearningRepository(config, agent)
            
            assert repository.storage_config is not None
            assert isinstance(repository.storage_config, FileStorageConfig)
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_codec_prefix_logic_with_codec(self):
        """Test codec prefix logic when codec is provided."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            assert repository._codec_prefix == "TestCodec"
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_codec_prefix_logic_without_codec(self):
        """Test codec prefix logic when codec is None."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config, codec=None)
            # Ensure codec is actually None
            agent._codec = None
            repository = LocalLearningRepository(config, agent)
            
            assert repository._codec_prefix == "default"
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_codec_prefix_logic_with_magic_codec(self):
        """Test codec prefix logic when codec has 'magic' in qualname."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            mock_codec = Mock()
            mock_codec.__qualname__ = "magic_codec"
            agent = MockAgent(storage_config=config, codec=mock_codec)
            repository = LocalLearningRepository(config, agent)
            
            assert repository._codec_prefix == "default"
        finally:
            shutil.rmtree(temp_dir)

    def test_initialization_calculates_base_storage_path(self):
        """Test initialization calculates correct base storage path."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            # Path should be: {workspace_folder}/{codec_prefix}/{agent.__class__.__qualname__}__{filename}
            # Check path structure (doesn't need to exist yet)
            path_str = str(repository._base_storage_path)
            assert "TestCodec" in path_str
            assert "MockAgent" in path_str
        finally:
            shutil.rmtree(temp_dir)


class TestLocalLearningRepositoryAcquisitive:
    """Test LocalLearningRepository acquisitive learning methods."""

    def test_save_acquisitive_loop_creates_session_folder(self):
        """Test save_acquisitive_loop creates session folder structure."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            loop_data = {
                "loop_id": "test-loop-123",
                "timestamp": datetime.now().isoformat(),
                "session_id": "test-session-001",
                "learning_note": "Test learning note",
            }
            
            session_id = "test-session-001"
            loop_id = "test-loop-123"
            timestamp = datetime.now()
            repository.save_acquisitive_loop(session_id, loop_data, loop_id, timestamp)
            
            acquisitive_path = repository._base_storage_path / "learnings" / session_id / "acquisitive"
            assert acquisitive_path.exists()
            assert acquisitive_path.is_dir()
        finally:
            shutil.rmtree(temp_dir)

    def test_save_acquisitive_loop_writes_json_file(self):
        """Test save_acquisitive_loop writes correct JSON file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            loop_data = {
                "loop_id": "test-loop-123",
                "timestamp": datetime(2024, 1, 15, 10, 30, 0).isoformat(),
                "session_id": "test-session-001",
                "learning_note": "Test learning note",
            }
            
            session_id = "test-session-001"
            loop_id = "test-loop-123"
            timestamp = datetime(2024, 1, 15, 10, 30, 0)
            repository.save_acquisitive_loop(session_id, loop_data, loop_id, timestamp)
            
            # Check file exists with correct pattern
            acquisitive_path = repository._base_storage_path / "learnings" / session_id / "acquisitive"
            loop_files = list(acquisitive_path.glob("loop_*.json"))
            assert len(loop_files) == 1
            
            # Verify JSON content
            loop_file = loop_files[0]
            loaded_data = json.loads(loop_file.read_text())
            assert loaded_data["loop_id"] == "test-loop-123"
            assert loaded_data["learning_note"] == "Test learning note"
        finally:
            shutil.rmtree(temp_dir)

    def test_load_acquisitive_loops_reads_correctly(self):
        """Test load_acquisitive_loops reads and extracts learning_note correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            # Save a loop
            loop_data = {
                "loop_id": "test-loop-123",
                "timestamp": datetime.now().isoformat(),
                "session_id": "test-session-001",
                "learning_note": "Test learning note",
            }
            
            session_id = "test-session-001"
            loop_id = "test-loop-123"
            timestamp = datetime.now()
            repository.save_acquisitive_loop(session_id, loop_data, loop_id, timestamp)
            
            # Load back
            learning_notes = repository.load_acquisitive_loops(session_id)
            
            assert len(learning_notes) == 1
            assert learning_notes[0] == "Test learning note"
        finally:
            shutil.rmtree(temp_dir)

    def test_load_acquisitive_loops_handles_multiple_loops(self):
        """Test load_acquisitive_loops handles multiple loops correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            session_id = "test-session-001"
            
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

    def test_load_acquisitive_loops_handles_missing_session(self):
        """Test load_acquisitive_loops handles missing session gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            # Try to load non-existent session
            learning_notes = repository.load_acquisitive_loops("non-existent-session")
            
            assert learning_notes == []
        finally:
            shutil.rmtree(temp_dir)

    def test_load_acquisitive_loops_handles_invalid_json(self):
        """Test load_acquisitive_loops handles invalid JSON gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            # Create session folder with invalid JSON
            acquisitive_path = repository._base_storage_path / "learnings" / "test-session-001" / "acquisitive"
            acquisitive_path.mkdir(parents=True, exist_ok=True)
            loop_file = acquisitive_path / "loop_20240115_103000_000000_test.json"
            loop_file.write_text("invalid json {")
            
            # Should not raise exception, just skip invalid files
            learning_notes = repository.load_acquisitive_loops("test-session-001")
            
            assert isinstance(learning_notes, list)
        finally:
            shutil.rmtree(temp_dir)

    def test_load_acquisitive_loops_filters_empty_learning_notes(self):
        """Test load_acquisitive_loops filters out loops without learning_note."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            session_id = "test-session-001"
            
            # Save loop with learning_note
            loop_data1 = {
                "loop_id": "test-loop-1",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "learning_note": "Valid learning note",
            }
            repository.save_acquisitive_loop(session_id, loop_data1, "test-loop-1", datetime.now())
            
            # Save loop without learning_note
            loop_data2 = {
                "loop_id": "test-loop-2",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
            }
            repository.save_acquisitive_loop(session_id, loop_data2, "test-loop-2", datetime.now())
            
            # Load back
            learning_notes = repository.load_acquisitive_loops(session_id)
            
            assert len(learning_notes) == 1
            assert learning_notes[0] == "Valid learning note"
        finally:
            shutil.rmtree(temp_dir)


class TestLocalLearningRepositoryEpisodic:
    """Test LocalLearningRepository episodic learning methods."""

    def test_save_episodic_learning_creates_session_folder(self):
        """Test save_episodic_learning creates session folder structure."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            content = "Test episodic learning content"
            session_id = "test-session-001"
            repository.save_episodic_learning(session_id, content)
            
            episodic_path = repository._base_storage_path / "learnings" / session_id / "episodic"
            assert episodic_path.exists()
            assert episodic_path.is_dir()
        finally:
            shutil.rmtree(temp_dir)

    def test_save_episodic_learning_writes_markdown_file(self):
        """Test save_episodic_learning writes correct markdown file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            content = "Test episodic learning content"
            session_id = "test-session-001"
            repository.save_episodic_learning(session_id, content)
            
            learnings_file = repository._base_storage_path / "learnings" / session_id / "episodic" / "learnings.md"
            assert learnings_file.exists()
            assert learnings_file.read_text() == content
        finally:
            shutil.rmtree(temp_dir)

    def test_load_episodic_learning_reads_correctly(self):
        """Test load_episodic_learning reads content correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            content = "Test episodic learning content"
            session_id = "test-session-001"
            repository.save_episodic_learning(session_id, content)
            
            # Load back
            loaded_content = repository.load_episodic_learning(session_id)
            
            assert loaded_content == content
        finally:
            shutil.rmtree(temp_dir)

    def test_load_episodic_learning_handles_missing_session(self):
        """Test load_episodic_learning handles missing session gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            # Try to load non-existent session
            loaded_content = repository.load_episodic_learning("non-existent-session")
            
            assert loaded_content is None
        finally:
            shutil.rmtree(temp_dir)

    def test_save_episodic_learning_overwrites_existing(self):
        """Test save_episodic_learning overwrites existing file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            session_id = "test-session-001"
            
            # Save first content
            repository.save_episodic_learning(session_id, "First content")
            
            # Save second content (should overwrite)
            repository.save_episodic_learning(session_id, "Second content")
            
            # Load back
            loaded_content = repository.load_episodic_learning(session_id)
            
            assert loaded_content == "Second content"
        finally:
            shutil.rmtree(temp_dir)


class TestLocalLearningRepositoryFeedback:
    """Test LocalLearningRepository feedback methods."""

    def test_save_feedback_creates_session_folder(self):
        """Test save_feedback creates session folder structure."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            content = "Test feedback content"
            session_id = "test-session-001"
            repository.save_feedback(session_id, content)
            
            feedback_path = repository._base_storage_path / "feedback" / session_id
            assert feedback_path.exists()
            assert feedback_path.is_dir()
        finally:
            shutil.rmtree(temp_dir)

    def test_save_feedback_writes_markdown_file(self):
        """Test save_feedback writes correct markdown file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            content = "Test feedback content"
            session_id = "test-session-001"
            repository.save_feedback(session_id, content)
            
            feedback_file = repository._base_storage_path / "feedback" / session_id / "feedback.md"
            assert feedback_file.exists()
            assert feedback_file.read_text() == content
        finally:
            shutil.rmtree(temp_dir)

    def test_load_feedback_reads_correctly(self):
        """Test load_feedback reads content correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            content = "Test feedback content"
            session_id = "test-session-001"
            repository.save_feedback(session_id, content)
            
            # Load back
            loaded_content = repository.load_feedback(session_id)
            
            assert loaded_content == content
        finally:
            shutil.rmtree(temp_dir)

    def test_load_feedback_handles_missing_session(self):
        """Test load_feedback handles missing session gracefully."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            # Try to load non-existent session
            loaded_content = repository.load_feedback("non-existent-session")
            
            assert loaded_content is None
        finally:
            shutil.rmtree(temp_dir)

    def test_save_feedback_overwrites_existing(self):
        """Test save_feedback overwrites existing file."""
        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent(storage_config=config)
            repository = LocalLearningRepository(config, agent)
            
            session_id = "test-session-001"
            
            # Save first content
            repository.save_feedback(session_id, "First feedback")
            
            # Save second content (should overwrite)
            repository.save_feedback(session_id, "Second feedback")
            
            # Load back
            loaded_content = repository.load_feedback(session_id)
            
            assert loaded_content == "Second feedback"
        finally:
            shutil.rmtree(temp_dir)

