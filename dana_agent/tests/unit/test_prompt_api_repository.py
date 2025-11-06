"""
Unit tests for LocalPromptAPI with repository pattern.

Tests that LocalPromptAPI creates repositories instead of stores.
"""

import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

# Mock the problematic import before any dana imports
sys.modules["dana.core.knowledge.prompts.agent_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.resource_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.workflow_prompt_engineer"] = MagicMock()

from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
from dana.core.resource.base_resource import BaseResource
from dana.core.knowledge.prompts.prompt_api import LocalPromptAPI
from dana.core.knowledge.prompts.codecs import CSXMLCodec
from dana.repositories.local_file_repository import LocalPromptRepository


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
            api = LocalPromptAPI(
                agent=agent,
                storage_config=config,
                codec=CSXMLCodec
            )
            
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
            api = LocalPromptAPI(
                agent=agent,
                storage_config=config,
                codec=CSXMLCodec
            )
            
            # Create a prompt engineer
            from dana.core.knowledge.prompts.prompt_engineer.base_prompt_engineer import ResourcePromptEngineer
            engineer = api._instantiate_prompt_engineer(
                ResourcePromptEngineer,
                component,
                relative_path="test/path"
            )
            
            # Verify engineer has repository, not store
            assert hasattr(engineer, '_repository')
            assert not hasattr(engineer, '_store')
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
            api = LocalPromptAPI(
                agent=agent,
                storage_config=config,
                codec=CSXMLCodec
            )
            
            from dana.core.knowledge.prompts.prompt_engineer.base_prompt_engineer import ResourcePromptEngineer
            engineer = api._instantiate_prompt_engineer(
                ResourcePromptEngineer,
                component,
                relative_path="test/path"
            )
            
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
            api = LocalPromptAPI(
                agent=agent,
                storage_config=config,
                codec=CSXMLCodec
            )
            
            # Verify _store is a repository
            assert isinstance(api._store, LocalPromptRepository)
            
            # Verify it can be used like a store (compatibility methods)
            api._store.create_snapshot(
                content="Test content",
                provenance={},
                metrics={}
            )
            api._store.set_active("v1")
            
            snapshot = api._store.get_active(error_if_not_found=False)
            assert snapshot is not None
            assert snapshot.content == "Test content"
        finally:
            shutil.rmtree(temp_dir)

