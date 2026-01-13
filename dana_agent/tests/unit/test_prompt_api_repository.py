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
from dana.core.knowledge.prompts.prompt_api import LocalPromptAPI
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

            # Create a factory with the custom config
            factory = RepositoryFactory()
            factory.register(RepositoryType.PROMPT, LocalPromptRepository, config)

            api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=factory)

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

            # Create a factory with the custom config
            factory = RepositoryFactory()
            factory.register(RepositoryType.PROMPT, LocalPromptRepository, config)

            api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=factory)

            # Create a prompt engineer
            from dana.core.knowledge.prompts.prompt_engineer.base_prompt_engineer import ResourcePromptEngineer

            engineer = api._instantiate_prompt_engineer(ResourcePromptEngineer, component, relative_path="test/path")

            # Verify engineer has repository, not store
            assert hasattr(engineer, "_repository")
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

            # Create a factory with the custom config
            factory = RepositoryFactory()
            factory.register(RepositoryType.PROMPT, LocalPromptRepository, config)

            api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=factory)

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

            # Create a factory with the custom config
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
    """Test LocalPromptAPI uses RepositoryFactory."""

    def test_initialization_uses_factory_to_create_repository(self):
        """Test that LocalPromptAPI uses RepositoryFactory to create system prompt repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()

            # Mock the factory
            mock_factory = Mock(spec=RepositoryFactory)
            mock_repository = Mock(spec=LocalPromptRepository)
            mock_factory.create.return_value = mock_repository

            api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

            # Verify factory.create was called with correct parameters
            mock_factory.create.assert_called_once_with(RepositoryType.PROMPT, agent=agent, component=None)

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

            # Mock the factory
            mock_factory = Mock(spec=RepositoryFactory)
            mock_repository = Mock(spec=LocalPromptRepository)
            mock_factory.create.return_value = mock_repository

            api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

            # Create a prompt engineer
            from dana.core.knowledge.prompts.prompt_engineer.base_prompt_engineer import ResourcePromptEngineer

            engineer = api._instantiate_prompt_engineer(ResourcePromptEngineer, component, relative_path="test/path")

            # Verify factory.create was called for component repository
            # Should be called twice: once for system prompt, once for component
            assert mock_factory.create.call_count >= 2

            # Check the last call was for the component
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
        agent = MockAgent()

        api = LocalPromptAPI(agent=agent, codec=CSXMLCodec)

        # Verify _store is a LocalPromptRepository (created by default factory)
        assert isinstance(api._store, LocalPromptRepository)
        assert api._store._agent == agent

    def test_factory_creates_repository_with_correct_type(self):
        """Test that factory creates PROMPT type repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()

            # Mock the factory
            mock_factory = Mock(spec=RepositoryFactory)
            mock_repository = Mock(spec=LocalPromptRepository)
            mock_factory.create.return_value = mock_repository

            LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=mock_factory)

            # Verify first positional arg is RepositoryType.PROMPT
            call_args = mock_factory.create.call_args
            assert call_args[0][0] == RepositoryType.PROMPT
        finally:
            shutil.rmtree(temp_dir)
