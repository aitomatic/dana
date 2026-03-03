"""
Unit tests for LocalPromptAPI with repository pattern.

Tests that LocalPromptAPI creates repositories instead of stores.
"""

import shutil
import sys
import tempfile
from unittest.mock import MagicMock, Mock


# Mock the problematic import before any dana imports
sys.modules["dana.core.knowledge.prompts.agent_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.resource_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.workflow_prompt_engineer"] = MagicMock()

from dana.config.storage_config import FileStorageConfig
from dana.core.agent.base_agent import BaseAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec
from dana.core.prompt.prompt_api import LocalPromptAPI
from dana.core.resource.base_resource import BaseResource
from dana.repositories.local_file_repository import LocalPromptRepository
from dana.repositories.repository_factory import RepositoryFactory, RepositoryType


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(self, **kwargs):
        super().__init__(agent_type="test_agent", agent_id="test-agent-123", **kwargs)
        self._codec = Mock()
        self._codec.__qualname__ = "TestCodec"


class MockResource(BaseResource):
    """Mock resource for testing."""

    def __init__(self, **kwargs):
        super().__init__(resource_type="test_resource", auto_register=False, **kwargs)


class TestLocalPromptAPIRepository:
    """Test LocalPromptAPI creates repositories instead of stores."""

    def test_initialization_creates_repository_instead_of_store(self):
        """Test that LocalPromptAPI creates LocalPromptRepository in __init__."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            api = LocalPromptAPI(agent=agent, storage_config=config, codec=CSXMLCodec)

            # Verify _store is actually a LocalPromptRepository
            assert isinstance(api._store, LocalPromptRepository)
            assert api._store._agent == agent
            assert api._store._component is None  # For system prompt template
        finally:
            shutil.rmtree(temp_dir)

    def test_instantiate_prompt_engineer_creates_repository(self):
        """Test that _instantiate_prompt_engineer creates repository for component."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            component = MockResource()
            config = FileStorageConfig(workspace_folder=temp_dir)
            api = LocalPromptAPI(agent=agent, storage_config=config, codec=CSXMLCodec)

            # Create a prompt engineer
            from dana.core.knowledge.prompts.prompt_engineer.base_prompt_engineer import ResourcePromptEngineer

            engineer = api._instantiate_prompt_engineer(ResourcePromptEngineer, component, relative_path="test/path")

            # Verify engineer has repository, not store
            assert hasattr(engineer, "_repository")
            assert not hasattr(engineer, "_store")
            assert isinstance(engineer._repository, LocalPromptRepository)
            assert engineer._repository._agent == agent
            assert engineer._repository._component == component
        finally:
            shutil.rmtree(temp_dir)

    def test_instantiate_prompt_engineer_passes_repository_to_engineer(self):
        """Test that repository is passed to prompt engineer constructor."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            component = MockResource()
            config = FileStorageConfig(workspace_folder=temp_dir)
            api = LocalPromptAPI(agent=agent, storage_config=config, codec=CSXMLCodec)

            from dana.core.knowledge.prompts.prompt_engineer.base_prompt_engineer import ResourcePromptEngineer

            engineer = api._instantiate_prompt_engineer(ResourcePromptEngineer, component, relative_path="test/path")

            # Verify repository is correctly bound
            assert engineer._repository._agent == agent
            assert engineer._repository._component == component
            assert engineer._component == component
        finally:
            shutil.rmtree(temp_dir)

    def test_system_prompt_store_is_repository(self):
        """Test that system prompt store is actually a repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)

            # Configure factory with the desired storage_config
            factory = RepositoryFactory()
            factory.register(RepositoryType.PROMPT, LocalPromptRepository, config)

            api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=factory)

            # Verify _store is a repository
            assert isinstance(api._store, LocalPromptRepository)

            # Verify it can be used like a store (compatibility methods)
            api._store.create_snapshot(content="Test content", provenance={}, metrics={})
            api._store.set_active("v1")

            snapshot = api._store.get_active(error_if_not_found=False)
            assert snapshot is not None
            assert snapshot.content == "Test content"
        finally:
            shutil.rmtree(temp_dir)


class TestLocalPromptAPIFactoryUsage:
    """Test LocalPromptAPI uses RepositoryFactory (TDD Step 1 - Red)."""

    def test_initialization_uses_factory_to_create_repository(self):
        """Test that LocalPromptAPI uses RepositoryFactory to create system prompt repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            FileStorageConfig(workspace_folder=temp_dir)

            # Mock the factory
            mock_factory = Mock(spec=RepositoryFactory)
            mock_repository = Mock(spec=LocalPromptRepository)
            mock_factory.create.return_value = mock_repository

            api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

            # Verify factory.create was called with correct parameters (without storage_config)
            mock_factory.create.assert_called_once_with(RepositoryType.PROMPT, agent=agent, component=None, provider=None)

            # Verify _store is the repository from factory
            assert api._store == mock_repository
        finally:
            shutil.rmtree(temp_dir)

    def test_instantiate_prompt_engineer_uses_factory(self):
        """Test that _instantiate_prompt_engineer uses factory to create repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            component = MockResource()
            config = FileStorageConfig(workspace_folder=temp_dir)

            # Mock the factory
            mock_factory = Mock(spec=RepositoryFactory)
            mock_repository = Mock(spec=LocalPromptRepository)
            mock_factory.create.return_value = mock_repository

            api = LocalPromptAPI(agent=agent, storage_config=config, codec=CSXMLCodec, repository_factory=mock_factory)

            # Create a prompt engineer
            from dana.core.knowledge.prompts.prompt_engineer.base_prompt_engineer import ResourcePromptEngineer

            engineer = api._instantiate_prompt_engineer(ResourcePromptEngineer, component, relative_path="test/path")

            # Verify factory.create was called for component repository
            # Should be called twice: once for system prompt, once for component
            assert mock_factory.create.call_count >= 2

            # Check the last call was for the component (without storage_config)
            last_call = mock_factory.create.call_args_list[-1]
            assert last_call[0][0] == RepositoryType.PROMPT
            assert last_call[1]["agent"] == agent
            assert last_call[1]["component"] == component

            # Verify engineer received repository from factory
            assert engineer._repository == mock_repository
        finally:
            shutil.rmtree(temp_dir)

    def test_uses_default_factory_when_not_provided(self):
        """Test that LocalPromptAPI uses DEFAULT_REPOSITORY_FACTORY when not provided."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)

            api = LocalPromptAPI(agent=agent, storage_config=config, codec=CSXMLCodec)

            # Verify _store is a LocalPromptRepository (created by default factory)
            assert isinstance(api._store, LocalPromptRepository)
            assert api._store._agent == agent
            # Note: When using default factory, it uses its own pre-configured storage_config,
            # not the one passed to LocalPromptAPI
            assert api._store.storage_config is not None
        finally:
            shutil.rmtree(temp_dir)

    def test_factory_passes_storage_config_correctly(self):
        """Test that storage_config is available in created repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)

            # Mock the factory
            mock_factory = Mock(spec=RepositoryFactory)
            mock_repository = Mock(spec=LocalPromptRepository)
            mock_repository.storage_config = config
            mock_factory.create.return_value = mock_repository

            api = LocalPromptAPI(agent=agent, storage_config=config, codec=CSXMLCodec, repository_factory=mock_factory)

            # Verify factory.create was called without storage_config parameter
            call_args = mock_factory.create.call_args
            assert "storage_config" not in call_args[1]

            # Verify the repository has the correct storage_config
            assert api._store.storage_config == config
        finally:
            shutil.rmtree(temp_dir)
