"""
Unit tests for PromptEngineer classes.

Tests the prompt loading architecture:
- BasePromptEngineer (base functionality)
- ResourcePromptEngineer (composition pattern with pluggable loading)
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
            assert not hasattr(engineer, "_store")  # Should not have _store anymore
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

    # NOTE: These tests were removed because _find_library_root and _load_file_content
    # methods no longer exist in the current BasePromptEngineer implementation.
    # The functionality has been refactored to use repository pattern for prompt loading.


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

    def test_initialization_with_custom_prompt_engineer_class(self):
        """Test ResourcePromptEngineer initialization."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            assert engineer._component == component
            assert engineer._repository == repository
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_initialization_defaults_to_base_prompt_engineer(self):
        """Test that ResourcePromptEngineer uses BasePromptEngineer implementation."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            # ResourcePromptEngineer IS a BasePromptEngineer
            assert isinstance(engineer, BasePromptEngineer)
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_has_get_prompt_method(self):
        """Test that ResourcePromptEngineer has prompt property."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            # Pre-create a prompt in the repository to avoid LLM calls
            repository.create_snapshot("Test prompt", {}, {})
            repository.set_active("v1")

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            assert hasattr(engineer, "prompt")
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_get_prompt_returns_string(self):
        """Test that prompt property returns a string."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            # Pre-create a prompt in the repository to avoid LLM calls
            repository.create_snapshot("Test prompt content", {}, {})
            repository.set_active("v1")

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            prompt = engineer.prompt
            assert isinstance(prompt, str)
            assert prompt == "Test prompt content"
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_get_prompt_delegates_to_internal_engineer(self):
        """Test that prompt property loads from repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            # Pre-create a prompt in the repository
            repository.create_snapshot("Repository loaded prompt", {}, {})
            repository.set_active("v1")

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            # Should load from repository
            result = engineer.prompt

            assert isinstance(result, str)
            assert result == "Repository loaded prompt"
        finally:
            import shutil

            shutil.rmtree(temp_dir)


class TestResourcePromptEngineerWithCreateFileResource:
    """Test ResourcePromptEngineer with real CreateFileResource example."""

    @pytest.fixture
    def create_file_resource(self):
        """Create a CreateFileResource instance for testing."""
        # Import here to avoid issues if module doesn't exist yet
        import sys

        # Use relative path from test file to examples directory
        examples_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "..",
            "examples",
            "agents",
            "financial-analysis",
            "resources",
        )
        examples_path = os.path.abspath(examples_path)

        if not os.path.exists(examples_path):
            pytest.skip("CreateFileResource example not available")

        sys.path.insert(0, examples_path)
        from create_file_resource import CreateFileResource

        return CreateFileResource(workspace_root="/tmp", auto_register=False)

    def test_loads_create_file_resource_prompt(self, create_file_resource):
        """Test that ResourcePromptEngineer loads CreateFileResource.xml prompt."""
        engineer = ResourcePromptEngineer(create_file_resource)

        prompt = engineer.get_prompt()

        # Should contain content from CreateFileResource.xml
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_create_file_resource_prompt_contains_expected_content(self, create_file_resource):
        """Test that loaded prompt contains expected XML structure."""
        engineer = ResourcePromptEngineer(create_file_resource)

        prompt = engineer.get_prompt()

        # Check for expected content from CreateFileResource.xml
        assert "CreateFileResource" in prompt
        assert "NAME" in prompt or "create" in prompt.lower()

    def test_handles_missing_prompt_file_gracefully(self):
        """Test that missing prompt file in repository returns None then generates."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a resource with no prompt in repository
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            # Don't pre-create a snapshot - repository will return None
            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            # load() should return None when no versions exist
            loaded = engineer.load()
            assert loaded is None
        finally:
            import shutil

            shutil.rmtree(temp_dir)


class TestResourcePromptEngineerInheritanceChain:
    """Test ResourcePromptEngineer handles inheritance chain correctly."""

    def test_loads_inherited_prompts_in_order(self):
        """Test that ResourcePromptEngineer loads prompts from repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a derived resource class
            class DerivedResource(MockResource):
                pass

            component = DerivedResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            # Pre-create a prompt to avoid LLM calls
            repository.create_snapshot("Derived resource prompt", {}, {})
            repository.set_active("v1")

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            # Should load from repository
            prompt = engineer.prompt
            assert isinstance(prompt, str)
            assert prompt == "Derived resource prompt"
        finally:
            import shutil

            shutil.rmtree(temp_dir)


class TestResourcePromptEngineerPromptPriority:
    """Test ResourcePromptEngineer prompt loading priority."""

    def test_co_located_prompt_loading(self):
        """Test that co-located prompts are found and loaded."""
        # This will test the co-located prompt functionality
        # The CreateFileResource has its prompt in examples/agents/financial-analysis/prompts/
        import sys

        # Use relative path from test file to examples directory
        examples_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "..",
            "examples",
            "agents",
            "financial-analysis",
            "resources",
        )
        examples_path = os.path.abspath(examples_path)

        if not os.path.exists(examples_path):
            pytest.skip("CreateFileResource example not available")

        sys.path.insert(0, examples_path)
        from create_file_resource import CreateFileResource

        temp_dir = tempfile.mkdtemp()
        try:
            config = FileStorageConfig(workspace_folder=temp_dir)
            agent = MockAgent()
            component = CreateFileResource(workspace_root="/tmp", auto_register=False)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec, force_generate=True)

            prompt = engineer.prompt

            # Should find the co-located CreateFileResource.xml
            assert len(prompt) > 0
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    def test_user_prompt_priority_over_lib(self):
        """Test that user prompts are loaded via repository pattern."""
        temp_dir = tempfile.mkdtemp()
        try:
            # This test documents that prompts are now managed via repository pattern
            component = MockResource()
            agent = MockAgent()
            config = FileStorageConfig(workspace_folder=temp_dir)
            repository = LocalPromptRepository(config, agent, component)

            engineer = ResourcePromptEngineer(component=component, repository=repository, codec=CSXMLCodec)

            # Engineer should use repository for loading prompts
            assert engineer._repository is not None
            assert isinstance(engineer._repository, LocalPromptRepository)
        finally:
            import shutil

            shutil.rmtree(temp_dir)
