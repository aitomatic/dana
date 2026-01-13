"""
Integration tests for LocalPromptAPI → PromptEngineer → LocalPromptRepository workflow.

Tests the full integration of the repository pattern migration.
"""

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

from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
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
        self._agents = []
        self._resources = []
        self._workflows = []


class MockResource(BaseResource):
    """Mock resource for testing."""

    def __init__(self, **kwargs):
        super().__init__(resource_type="test_resource", auto_register=False, **kwargs)


@pytest.mark.live
class TestPromptAPIRepositoryIntegration:
    """Integration tests for API → Engineer → Repository workflow."""

    def test_full_workflow_api_engineer_repository(self):
        """Test full workflow: API creates repository, passes to engineer, engineer uses repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            component = MockResource()
            agent._resources = [component]
            config = FileStorageConfig(workspace_folder=temp_dir)

            # Create a custom factory with the test's storage config
            factory = RepositoryFactory()
            factory.register(RepositoryType.PROMPT, LocalPromptRepository, config)

            api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=factory)

            # Verify API creates repository
            assert isinstance(api._store, LocalPromptRepository)

            # Call available_tools_prompt to trigger engineer creation (lazy initialization)
            _ = api.available_tools_prompt

            # Verify engineer was created with repository
            assert component in api._resource_prompt_engineers
            engineer = api._resource_prompt_engineers[component]

            # Verify engineer uses repository
            assert hasattr(engineer, "_repository")
            assert isinstance(engineer._repository, LocalPromptRepository)
            assert engineer._repository._agent == agent
            assert engineer._repository._component == component

            # Verify repository path is correct
            repo_path = engineer._repository._get_relative_prompt_path()
            expected_path = Path(temp_dir) / "TestCodec" / agent.object_id / "prompts" / "resources" / str(component.object_id)
            assert repo_path == expected_path
        finally:
            shutil.rmtree(temp_dir)

    def test_system_prompt_uses_repository(self):
        """Test that system prompt uses repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)

            # Create a custom factory with the test's storage config
            factory = RepositoryFactory()
            factory.register(RepositoryType.PROMPT, LocalPromptRepository, config)

            api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=factory)

            # Verify system prompt repository
            assert isinstance(api._store, LocalPromptRepository)
            assert api._store._agent == agent
            assert api._store._component is None  # System prompt template

            # Verify repository path for system prompt
            repo_path = api._store._get_relative_prompt_path()
            expected_path = Path(temp_dir) / "TestCodec" / agent.object_id / "prompts" / "system_prompt_template"
            assert repo_path == expected_path

            # Test persist and load
            api._template = "Test template"
            api.persist()

            # Verify repository was used
            assert api._store.has_any_versions()
            snapshot = api._store.get_active()
            assert snapshot.content == "Test template"

            # Test load
            loaded = api.load()
            assert loaded == "Test template"
        finally:
            shutil.rmtree(temp_dir)

    def test_resource_engineer_uses_repository(self):
        """Test that resource engineer uses repository correctly."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            component = MockResource()
            agent._resources = [component]
            config = FileStorageConfig(workspace_folder=temp_dir)

            # Create a custom factory with the test's storage config
            factory = RepositoryFactory()
            factory.register(RepositoryType.PROMPT, LocalPromptRepository, config)

            api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=factory)

            # Call available_tools_prompt to trigger engineer creation (lazy initialization)
            _ = api.available_tools_prompt

            engineer = api._resource_prompt_engineers[component]

            # Test engineer persist
            engineer._prompt = "Test resource prompt"
            engineer.persist()

            # Verify repository was used
            assert engineer._repository.has_any_versions()
            snapshot = engineer._repository.get_active()
            assert snapshot.content == "Test resource prompt"

            # Test engineer load
            loaded = engineer.load()
            assert loaded == "Test resource prompt"
        finally:
            shutil.rmtree(temp_dir)

    def test_file_structure_matches_repository_pattern(self):
        """Test that file structure created by repository matches expected pattern."""
        temp_dir = tempfile.mkdtemp()
        try:
            agent = MockAgent()
            component = MockResource()
            agent._resources = [component]
            config = FileStorageConfig(workspace_folder=temp_dir)

            # Create a custom factory with the test's storage config
            factory = RepositoryFactory()
            factory.register(RepositoryType.PROMPT, LocalPromptRepository, config)

            api = LocalPromptAPI(agent=agent, codec=CSXMLCodec, repository_factory=factory)

            # Create some prompts
            api._template = "System template"
            api.persist()

            # Call available_tools_prompt to trigger engineer creation (lazy initialization)
            _ = api.available_tools_prompt

            engineer = api._resource_prompt_engineers[component]
            engineer._prompt = "Resource prompt"
            engineer.persist()

            # Verify file structure
            system_path = Path(temp_dir) / "TestCodec" / agent.object_id / "prompts" / "system_prompt_template"
            resource_path = Path(temp_dir) / "TestCodec" / agent.object_id / "prompts" / "resources" / str(component.object_id)

            assert system_path.exists()
            assert resource_path.exists()

            # Verify versions folders exist
            assert (system_path / "versions").exists()
            assert (resource_path / "versions").exists()

            # Verify version files exist
            assert (system_path / "versions" / "v1.prompt").exists()
            assert (resource_path / "versions" / "v1.prompt").exists()
        finally:
            shutil.rmtree(temp_dir)
