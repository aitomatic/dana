"""
Unit tests for LangfusePromptRepository.

Tests the Langfuse-based prompt repository with mocked Langfuse SDK.
"""

from datetime import UTC, datetime
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest


# Mock the problematic import before any dana imports
sys.modules["dana.core.knowledge.prompts.agent_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.resource_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.workflow_prompt_engineer"] = MagicMock()

# Now import normally
from dana.config.storage_config import LangfuseStorageConfig
from dana.core.agent import BaseAgent
from dana.core.resource import BaseResource
from dana.core.workflow import BaseWorkflow
from dana.repositories.langfuse_repository import LangfusePromptRepository


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(self, **kwargs):
        super().__init__(agent_type="test_agent", agent_id="test-agent-123", **kwargs)
        # Mock codec
        self._codec = Mock()
        self._codec.__qualname__ = "TestCodec"


class MockResource(BaseResource):
    """Mock resource for testing."""

    def __init__(self, **kwargs):
        super().__init__(resource_type="test_resource", auto_register=False, **kwargs)


class MockWorkflow(BaseWorkflow):
    """Mock workflow for testing."""

    def __init__(self, **kwargs):
        super().__init__(workflow_type="test_workflow", auto_register=False, **kwargs)


class TestLangfusePromptRepositoryInitialization:
    """Test LangfusePromptRepository initialization."""

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_initialization_with_agent_and_component(self, mock_get_client):
        """Test initialization with agent and component."""
        # Mock Langfuse client
        mock_langfuse = MagicMock()
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        component = MockResource()

        repository = LangfusePromptRepository(config, agent, component)

        assert repository._agent == agent
        assert repository._component == component
        assert repository._langfuse == mock_langfuse
        assert repository._prompt_name is not None
        mock_get_client.assert_called_once()

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_initialization_with_agent_only(self, mock_get_client):
        """Test initialization with agent only (component=None)."""
        # Mock Langfuse client
        mock_langfuse = MagicMock()
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()

        repository = LangfusePromptRepository(config, agent, component=None)

        assert repository._agent == agent
        assert repository._component is None
        assert "system_prompt_template" in repository._prompt_name

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_prompt_name_generation(self, mock_get_client):
        """Test prompt name generation using mixin methods."""
        # Mock Langfuse client
        mock_langfuse = MagicMock()
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        component = MockResource()

        repository = LangfusePromptRepository(config, agent, component)

        # Check prompt name format - uses object_id for component
        assert "TestCodec" in repository._prompt_name
        assert "resources" in repository._prompt_name


class TestLangfusePromptRepositoryCreateSnapshot:
    """Test LangfusePromptRepository create_snapshot method."""

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_create_snapshot_first_version(self, mock_get_client):
        """Test creating first snapshot (v1)."""
        # Mock Langfuse client
        mock_langfuse = MagicMock()
        mock_langfuse.get_prompt.return_value = None  # No existing prompt
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        content = "Test prompt content"
        provenance = {"source": "test"}
        metrics = {"test_metric": 1}

        snapshot = repository.create_snapshot(content, provenance, metrics)

        assert snapshot.version == "v1"
        assert snapshot.content == content
        assert snapshot.provenance == provenance
        assert snapshot.metrics == metrics
        mock_langfuse.create_prompt.assert_called()
        mock_langfuse.flush.assert_called_once()

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_create_snapshot_increments_version(self, mock_get_client):
        """Test creating snapshot increments version number."""
        # Mock Langfuse client with existing prompt
        mock_langfuse = MagicMock()
        mock_existing_prompt = MagicMock()
        mock_existing_prompt.config = {"dana_versions": ["v1", "v2"]}
        mock_langfuse.get_prompt.return_value = mock_existing_prompt
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        content = "Test prompt content v3"
        provenance = {"source": "test"}
        metrics = {}

        snapshot = repository.create_snapshot(content, provenance, metrics)

        assert snapshot.version == "v3"
        mock_langfuse.create_prompt.assert_called()
        mock_langfuse.flush.assert_called_once()


class TestLangfusePromptRepositoryLoadSnapshot:
    """Test LangfusePromptRepository load_snapshot method."""

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_load_snapshot_success(self, mock_get_client):
        """Test loading snapshot successfully."""
        # Mock Langfuse client with prompt
        mock_langfuse = MagicMock()
        mock_prompt = MagicMock()
        mock_prompt.prompt = "Test prompt content"
        mock_prompt.content = "Test prompt content"
        mock_prompt.config = {"provenance": {"source": "test"}, "metrics": {"test_metric": 1}}
        mock_prompt.created_at = datetime.now(UTC)
        mock_prompt.updated_at = datetime.now(UTC)
        mock_langfuse.get_prompt.return_value = mock_prompt
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        snapshot = repository.load_snapshot("v1")

        assert snapshot is not None
        assert snapshot.version == "v1"
        assert snapshot.content == "Test prompt content"
        assert snapshot.provenance == {"source": "test"}
        assert snapshot.metrics == {"test_metric": 1}

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_load_snapshot_not_found(self, mock_get_client):
        """Test loading snapshot when version not found."""
        # Mock Langfuse client returning None
        mock_langfuse = MagicMock()
        mock_langfuse.get_prompt.return_value = None
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        with pytest.raises(ValueError, match="Version v1 not found"):
            repository.load_snapshot("v1", error_if_not_found=True)

        # Test with error_if_not_found=False
        snapshot = repository.load_snapshot("v1", error_if_not_found=False)
        assert snapshot is None


class TestLangfusePromptRepositoryListVersions:
    """Test LangfusePromptRepository list_versions method."""

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_list_versions_success(self, mock_get_client):
        """Test listing versions successfully."""
        # Mock Langfuse client with prompt containing versions
        mock_langfuse = MagicMock()
        mock_prompt = MagicMock()
        mock_prompt.config = {"dana_versions": ["v1", "v2", "v3"]}
        mock_langfuse.get_prompt.return_value = mock_prompt
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        versions = repository.list_versions()

        assert versions == ["v1", "v2", "v3"]

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_list_versions_empty(self, mock_get_client):
        """Test listing versions when no versions exist."""
        # Mock Langfuse client with prompt but no versions
        mock_langfuse = MagicMock()
        mock_prompt = MagicMock()
        mock_prompt.config = {}
        mock_langfuse.get_prompt.return_value = mock_prompt
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        versions = repository.list_versions()

        assert versions == []

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_list_versions_no_prompt(self, mock_get_client):
        """Test listing versions when prompt doesn't exist."""
        # Mock Langfuse client returning None
        mock_langfuse = MagicMock()
        mock_langfuse.get_prompt.return_value = None
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        versions = repository.list_versions()

        assert versions == []


class TestLangfusePromptRepositoryGetActive:
    """Test LangfusePromptRepository get_active method."""

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_get_active_with_metadata(self, mock_get_client):
        """Test getting active version from metadata."""
        # Mock Langfuse client with prompt containing active version
        mock_langfuse = MagicMock()
        mock_base_prompt = MagicMock()
        mock_base_prompt.config = {"dana_active_version": "v2", "dana_versions": ["v1", "v2"]}
        mock_version_prompt = MagicMock()
        mock_version_prompt.prompt = "Active prompt content"
        mock_version_prompt.config = {"provenance": {}, "metrics": {}}
        mock_version_prompt.created_at = datetime.now(UTC)
        mock_version_prompt.updated_at = datetime.now(UTC)

        def get_prompt_side_effect(name, label=None):
            if label is None:
                return mock_base_prompt
            elif label == "v2":
                return mock_version_prompt
            return None

        mock_langfuse.get_prompt.side_effect = get_prompt_side_effect
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        snapshot = repository.get_active()

        assert snapshot is not None
        assert snapshot.version == "v2"
        assert snapshot.content == "Active prompt content"

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_get_active_fallback_to_latest(self, mock_get_client):
        """Test getting active version falls back to latest when no active set."""
        # Mock Langfuse client with versions but no active version
        mock_langfuse = MagicMock()
        mock_base_prompt = MagicMock()
        mock_base_prompt.config = {"dana_versions": ["v1", "v2"]}
        mock_version_prompt = MagicMock()
        mock_version_prompt.prompt = "Latest prompt content"
        mock_version_prompt.config = {"provenance": {}, "metrics": {}}
        mock_version_prompt.created_at = datetime.now(UTC)
        mock_version_prompt.updated_at = datetime.now(UTC)

        def get_prompt_side_effect(name, label=None):
            if label is None:
                return mock_base_prompt
            elif label == "v2":
                return mock_version_prompt
            return None

        mock_langfuse.get_prompt.side_effect = get_prompt_side_effect
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        snapshot = repository.get_active()

        assert snapshot is not None
        assert snapshot.version == "v2"  # Latest version


class TestLangfusePromptRepositorySetActive:
    """Test LangfusePromptRepository set_active method."""

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_set_active_version(self, mock_get_client):
        """Test setting active version."""
        # Mock Langfuse client
        mock_langfuse = MagicMock()
        mock_version_prompt = MagicMock()
        mock_version_prompt.prompt = "Version prompt content"
        mock_version_prompt.config = {}
        mock_base_prompt = MagicMock()
        mock_base_prompt.config = {}

        def get_prompt_side_effect(name, label=None):
            if label == "v1":
                return mock_version_prompt
            elif label is None:
                return mock_base_prompt
            return None

        mock_langfuse.get_prompt.side_effect = get_prompt_side_effect
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        repository.set_active("v1")

        # Verify active version was set in cache
        assert repository._active_version_cache == "v1"
        # Verify get_prompt was called
        mock_langfuse.get_prompt.assert_called()


class TestLangfusePromptRepositoryHasAnyVersions:
    """Test LangfusePromptRepository has_any_versions method."""

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_has_any_versions_true(self, mock_get_client):
        """Test has_any_versions returns True when versions exist."""
        # Mock Langfuse client with versions
        mock_langfuse = MagicMock()
        mock_prompt = MagicMock()
        mock_prompt.config = {"dana_versions": ["v1"]}
        mock_langfuse.get_prompt.return_value = mock_prompt
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        assert repository.has_any_versions() is True

    @patch("dana.repositories.langfuse_repository._get_langfuse_client")
    def test_has_any_versions_false(self, mock_get_client):
        """Test has_any_versions returns False when no versions exist."""
        # Mock Langfuse client with no versions
        mock_langfuse = MagicMock()
        mock_prompt = MagicMock()
        mock_prompt.config = {}
        mock_langfuse.get_prompt.return_value = mock_prompt
        mock_get_client.return_value = mock_langfuse

        config = LangfuseStorageConfig(public_key="test_key", secret_key="test_secret")
        agent = MockAgent()
        repository = LangfusePromptRepository(config, agent)

        assert repository.has_any_versions() is False
