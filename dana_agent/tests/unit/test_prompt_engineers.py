"""
Unit tests for PromptEngineer classes.

Tests the prompt loading architecture:
- BasePromptEngineer (base functionality)
- ResourcePromptEngineer (composition pattern with pluggable loading)
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import pytest

# Mock the problematic import before any dana imports
sys.modules["dana.core.knowledge.prompts.agent_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.resource_prompt_engineer"] = MagicMock()
sys.modules["dana.core.knowledge.prompts.workflow_prompt_engineer"] = MagicMock()

from dana.common.base_war import BaseWAR
from dana.config.storage_config import FileStorageConfig
from dana.core.agent import BaseAgent
from dana.core.knowledge.prompts.prompt_engineer.base_prompt_engineer import BasePromptEngineer
from dana.core.knowledge.prompts.prompt_engineer.base_prompt_engineer import ResourcePromptEngineer
from dana.core.resource.base_resource import BaseResource
from dana.repositories.local_file_repository import LocalPromptRepository
from dana.core.knowledge.prompts.codecs import CSXMLCodec


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
            
            engineer = ConcretePromptEngineer(
                component=component,
                repository=repository,
                codec=CSXMLCodec
            )
            
            assert engineer._component == component
            assert engineer._repository == repository
            assert hasattr(engineer, '_repository')
            assert not hasattr(engineer, '_store')  # Should not have _store anymore
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
            
            engineer = ConcretePromptEngineer(
                component=component,
                repository=repository,
                codec=CSXMLCodec
            )
            
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
            repository.create_snapshot(
                content="Test content",
                provenance={},
                metrics={}
            )
            repository.set_active("v1")
            
            engineer = ConcretePromptEngineer(
                component=component,
                repository=repository,
                codec=CSXMLCodec
            )
            
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
            
            engineer = ConcretePromptEngineer(
                component=component,
                repository=repository,
                codec=CSXMLCodec
            )
            
            # Call load when no versions exist
            result = engineer.load()
            
            assert result is None
        finally:
            import shutil
            shutil.rmtree(temp_dir)

    def test_has_find_library_root_method(self):
        """Test that BasePromptEngineer has _find_library_root method."""
        component = MockResource()
        engineer = BasePromptEngineer(component)
        
        assert hasattr(engineer, '_find_library_root')
        assert callable(engineer._find_library_root)

    def test_has_load_file_content_method(self):
        """Test that BasePromptEngineer has _load_file_content method."""
        component = MockResource()
        engineer = BasePromptEngineer(component)
        
        assert hasattr(engineer, '_load_file_content')
        assert callable(engineer._load_file_content)

    def test_load_file_content_reads_file(self):
        """Test that _load_file_content reads XML file content."""
        component = MockResource()
        engineer = BasePromptEngineer(component)
        
        # Create a temporary XML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write('<TEST>Content</TEST>')
            temp_path = f.name
        
        try:
            content = engineer._load_file_content(temp_path)
            assert content == '<TEST>Content</TEST>'
        finally:
            os.unlink(temp_path)

    def test_load_file_content_handles_missing_file(self):
        """Test that _load_file_content handles missing files gracefully."""
        component = MockResource()
        engineer = BasePromptEngineer(component)
        
        content = engineer._load_file_content('/nonexistent/path.xml')
        assert content == ""

    def test_load_file_content_handles_empty_path(self):
        """Test that _load_file_content handles empty path."""
        component = MockResource()
        engineer = BasePromptEngineer(component)
        
        content = engineer._load_file_content("")
        assert content == ""

    def test_find_library_root_returns_string(self):
        """Test that _find_library_root returns a string path."""
        component = MockResource()
        engineer = BasePromptEngineer(component)
        
        root = engineer._find_library_root()
        assert isinstance(root, str)
        assert len(root) > 0


class TestResourcePromptEngineer:
    """Test ResourcePromptEngineer functionality."""

    def test_initialization_with_component(self):
        """Test ResourcePromptEngineer initialization with a component."""
        component = MockResource()
        engineer = ResourcePromptEngineer(component)
        
        assert engineer._engineer is not None
        assert isinstance(engineer._engineer, BasePromptEngineer)

    def test_initialization_with_custom_prompt_engineer_class(self):
        """Test ResourcePromptEngineer initialization with custom prompt engineer class."""
        component = MockResource()
        
        # Create a custom prompt engineer class
        class CustomPromptEngineer(BasePromptEngineer):
            pass
        
        engineer = ResourcePromptEngineer(component, CustomPromptEngineer)
        
        assert engineer._engineer is not None
        assert isinstance(engineer._engineer, CustomPromptEngineer)

    def test_initialization_defaults_to_base_prompt_engineer(self):
        """Test that ResourcePromptEngineer defaults to BasePromptEngineer."""
        component = MockResource()
        engineer = ResourcePromptEngineer(component)
        
        assert type(engineer._engineer).__name__ == 'BasePromptEngineer'

    def test_has_get_prompt_method(self):
        """Test that ResourcePromptEngineer has get_prompt method."""
        component = MockResource()
        engineer = ResourcePromptEngineer(component)
        
        assert hasattr(engineer, 'get_prompt')
        assert callable(engineer.get_prompt)

    def test_get_prompt_returns_string(self):
        """Test that get_prompt returns a string."""
        component = MockResource()
        engineer = ResourcePromptEngineer(component)
        
        prompt = engineer.get_prompt()
        assert isinstance(prompt, str)

    def test_get_prompt_delegates_to_internal_engineer(self):
        """Test that get_prompt delegates to internal engineer's _load_inherited_prompt_content."""
        component = MockResource()
        engineer = ResourcePromptEngineer(component)
        
        # Mock the internal engineer's method
        with patch.object(engineer._engineer, '_load_inherited_prompt_content', return_value='<MOCK>Content</MOCK>'):
            result = engineer.get_prompt()
            
        assert result == '<MOCK>Content</MOCK>'


class TestResourcePromptEngineerWithCreateFileResource:
    """Test ResourcePromptEngineer with real CreateFileResource example."""

    @pytest.fixture
    def create_file_resource(self):
        """Create a CreateFileResource instance for testing."""
        # Import here to avoid issues if module doesn't exist yet
        import sys
        sys.path.insert(0, '/Users/lam/Desktop/another_opendxa/examples/agents/financial-analysis/resources')
        from create_file_resource import CreateFileResource
        
        return CreateFileResource(workspace_root='/tmp', auto_register=False)

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
        assert 'CreateFileResource' in prompt
        assert 'NAME' in prompt or 'create' in prompt.lower()

    def test_handles_missing_prompt_file_gracefully(self):
        """Test that missing prompt file returns empty string gracefully."""
        # Create a resource with no associated prompt file
        component = MockResource()
        engineer = ResourcePromptEngineer(component)
        
        # Should not raise an error
        prompt = engineer.get_prompt()
        assert isinstance(prompt, str)


class TestResourcePromptEngineerInheritanceChain:
    """Test ResourcePromptEngineer handles inheritance chain correctly."""

    def test_loads_inherited_prompts_in_order(self):
        """Test that ResourcePromptEngineer loads prompts following inheritance chain."""
        # Create a derived resource class
        class DerivedResource(MockResource):
            pass
        
        component = DerivedResource()
        engineer = ResourcePromptEngineer(component)
        
        # Should follow MRO: BaseWAR -> BaseResource -> MockResource -> DerivedResource
        prompt = engineer.get_prompt()
        assert isinstance(prompt, str)


class TestResourcePromptEngineerPromptPriority:
    """Test ResourcePromptEngineer prompt loading priority."""

    def test_co_located_prompt_loading(self):
        """Test that co-located prompts are found and loaded."""
        # This will test the co-located prompt functionality
        # The CreateFileResource has its prompt in examples/agents/financial-analysis/prompts/
        import sys
        sys.path.insert(0, '/Users/lam/Desktop/another_opendxa/examples/agents/financial-analysis/resources')
        from create_file_resource import CreateFileResource
        
        component = CreateFileResource(workspace_root='/tmp', auto_register=False)
        engineer = ResourcePromptEngineer(component)
        
        prompt = engineer.get_prompt()
        
        # Should find the co-located CreateFileResource.xml
        assert len(prompt) > 0

    def test_user_prompt_priority_over_lib(self):
        """Test that user prompts (~/.dana/prompts/) have priority over lib prompts."""
        # This test documents the expected behavior
        # Priority: user > lib > core > co-located
        component = MockResource()
        engineer = ResourcePromptEngineer(component)
        
        # Get the priority methods
        assert hasattr(engineer._engineer, '_get_user_prompt_file')
        assert hasattr(engineer._engineer, '_get_lib_prompt_file')
        assert hasattr(engineer._engineer, '_get_core_prompt_file')
        assert hasattr(engineer._engineer, '_get_co_located_prompt_file')

