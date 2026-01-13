"""
Unit tests for PromptEngineer classes.

Tests the prompt loading architecture:
- BasePromptEngineer (base functionality via ConcretePromptEngineer)
- ResourcePromptEngineer (formats @tool_use methods)
"""

import os
import sys
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest


# Mock the problematic import before any dana imports
sys.modules["dana.core.knowledge.prompts.agent_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.resource_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.workflow_prompt_engineer"] = MagicMock()

from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec
from dana.core.knowledge.prompts.prompt_engineer.base_prompt_engineer import BasePromptEngineer, ResourcePromptEngineer
from dana.core.resource.base_resource import BaseResource
from dana.repositories.local_file_repository import LocalPromptRepository


class MockResource(BaseResource):
    """Mock resource for testing."""

    def __init__(self, **kwargs):
        super().__init__(resource_type="mock", auto_register=False, **kwargs)


class MockAgent(BaseAgent):
    """Mock agent for testing."""

    def __init__(self, **kwargs):
        super().__init__(agent_type="test_agent", agent_id="test-agent-123", **kwargs)
        self._codec = Mock()
        self._codec.__qualname__ = "TestCodec"


class ConcretePromptEngineer(BasePromptEngineer):
    """Concrete implementation for testing BasePromptEngineer."""

    def construct_prompt(self) -> str:
        return "Test prompt"

    def check_conflicts(self) -> bool:
        return False


class TestBasePromptEngineer:
    """Test BasePromptEngineer functionality."""

    def test_initialization_with_repository(self):
        """Test BasePromptEngineer initialization with repository parameter."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ConcretePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            assert engineer._component == component
            assert engineer._repository == repository
            assert hasattr(engineer, "_repository")
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_persist_uses_repository_create_snapshot(self):
        """Test persist() calls repository.create_snapshot()."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ConcretePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            # Set prompt content
            engineer._prompt = "Test prompt content"

            # Call persist
            engineer.persist()

            # Verify repository was used
            assert repository.has_any_versions()
            snapshot = repository.get_active()
            assert snapshot.content == "Test prompt content"
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_load_uses_repository_get_active(self):
        """Test load() calls repository.get_active()."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            # Create a version first
            repository.create_snapshot(content="Test content", provenance={}, metrics={})
            repository.set_active("v1")

            engineer = ConcretePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            # Call load
            result = engineer.load()

            assert result == "Test content"
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_load_returns_none_when_no_versions(self):
        """Test load() returns None when no versions exist."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ConcretePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            # Call load when no versions exist
            result = engineer.load()

            assert result is None
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_prompt_property_calls_get_prompt(self):
        """Test that prompt property calls _get_prompt."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ConcretePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            # Access prompt property
            prompt = engineer.prompt

            # Should call construct_prompt since no existing versions
            assert prompt == "Test prompt"
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_force_generate_regenerates_prompt(self):
        """Test that force_generate=True regenerates the prompt."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            # Create an existing version
            repository.create_snapshot(content="Old content", provenance={}, metrics={})
            repository.set_active("v1")

            engineer = ConcretePromptEngineer(
                component=component, repository=repository, codec=CSXMLCodec, force_generate=True
            )

            # Access prompt - should regenerate despite existing version
            prompt = engineer.prompt

            assert prompt == "Test prompt"
        finally:
            import shutil

            shutil.rmtree(temp_dir)


@pytest.mark.live
class TestResourcePromptEngineer:
    """Test ResourcePromptEngineer functionality."""

    def test_initialization_with_component(self):
        """Test ResourcePromptEngineer initialization with a component."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            assert engineer._component == component
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_construct_prompt_passes_object_id(self):
        """Test that construct_prompt passes object_id to parse_method_signature."""
        from unittest.mock import MagicMock, patch

        from dana.common.protocols.war import tool_use

        class TestResourceWithTool(BaseResource):
            def __init__(self, **kwargs):
                super().__init__(resource_type="test", resource_id="my-test-resource", auto_register=False, **kwargs)

            @tool_use
            def search(self, query: str) -> dict:
                """Search method.

                Args:
                    query: Search query
                """
                return {"query": query}

        temp_dir = tempfile.mkdtemp()
        try:
            component = TestResourceWithTool()
            # Mock llm_client to avoid connection errors
            component._llm_client = MagicMock()

            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec, force_generate=True)

            # Mock parse_method_signature to verify object_id is passed
            with patch("dana.common.utils.misc.Misc.parse_method_signature") as mock_parse:
                from dana.common.schemas.tool_call import MethodSignature, ParameterInfo

                mock_signature = MethodSignature(
                    name="search",
                    object_id=None,
                    class_name="TestResourceWithTool",
                    description="Search method.",
                    parameters=[ParameterInfo(name="query", type="str", description="Search query", has_default=False)],
                )
                mock_parse.return_value = mock_signature

                engineer.construct_prompt()

                # Verify parse_method_signature was called with object_id
                assert mock_parse.called
                call_args = mock_parse.call_args
                assert "object_id" in call_args.kwargs
                assert call_args.kwargs["object_id"] == component.object_id
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_construct_prompt_returns_string(self):
        """Test that construct_prompt returns a string."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            prompt = engineer.construct_prompt()
            assert isinstance(prompt, str)
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_check_conflicts_returns_false_for_no_conflicts(self):
        """Test that check_conflicts returns False when no conflicts."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            result = engineer.check_conflicts()
            assert result is False
        finally:
            import shutil

            shutil.rmtree(temp_dir)


@pytest.mark.live
class TestResourcePromptEngineerWithToolUse:
    """Test ResourcePromptEngineer with @tool_use decorated methods."""

    def test_formats_tool_use_methods(self):
        """Test that ResourcePromptEngineer formats @tool_use methods."""
        from dana.common.protocols.war import tool_use

        class TestResourceWithTools(BaseResource):
            def __init__(self, **kwargs):
                super().__init__(resource_type="test", auto_register=False, **kwargs)

            @tool_use
            def search(self, query: str) -> dict:
                """Search for items.

                Args:
                    query: Search query string
                """
                return {"query": query}

            @tool_use
            def create(self, name: str, value: int) -> dict:
                """Create a new item.

                Args:
                    name: Item name
                    value: Item value
                """
                return {"name": name, "value": value}

        temp_dir = tempfile.mkdtemp()
        try:
            component = TestResourceWithTools()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            prompt = engineer.construct_prompt()

            # Should contain method names
            assert "search" in prompt or "create" in prompt
            assert isinstance(prompt, str)
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_resource_with_no_tools(self):
        """Test ResourcePromptEngineer with resource that has no @tool_use methods."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()  # Has no @tool_use methods
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            prompt = engineer.construct_prompt()

            # Should return resource description or empty string
            assert isinstance(prompt, str)
        finally:
            import shutil

            shutil.rmtree(temp_dir)
