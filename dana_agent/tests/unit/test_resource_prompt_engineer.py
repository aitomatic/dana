"""
Unit tests for ResourcePromptEngineer.

Tests the prompt engineering for resources that formats @tool_use decorated methods
using the configured codec (CSXMLCodec or KLXMLCodec).
"""

from unittest.mock import Mock

import pytest

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.common.storage import AbstractStorage
from dana.core.knowledge.prompts.codecs import CSXMLCodec, KLXMLCodec
from dana.core.knowledge.prompts.resource_prompt_engineer import ResourcePromptEngineer
from dana.core.resource.base_resource import BaseResource


class MockResourceWithTool(BaseResource):
    """Mock resource with @tool_use decorated method for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(resource_type="mock", auto_register=False, **kwargs)
    
    @tool_use
    def test_method(self, param1: str) -> DictParams:
        """Test method with one parameter."""
        return {"result": param1}


class MockResourceWithoutTool(BaseResource):
    """Mock resource without @tool_use decorated methods."""
    
    def __init__(self, **kwargs):
        super().__init__(resource_type="mock_no_tool", auto_register=False, **kwargs)
    
    def regular_method(self):
        """Regular method without @tool_use."""
        pass


class MockResourceMultipleTools(BaseResource):
    """Mock resource with multiple @tool_use decorated methods."""
    
    def __init__(self, **kwargs):
        super().__init__(resource_type="mock_multi", auto_register=False, **kwargs)
    
    @tool_use
    def method_one(self, param1: str) -> DictParams:
        """First tool method."""
        return {"result": param1}
    
    @tool_use
    def method_two(self, param2: int) -> DictParams:
        """Second tool method."""
        return {"result": param2}
    
    @tool_use
    def method_three(self, param3: bool = True) -> DictParams:
        """Third tool method with default."""
        return {"result": param3}


class TestResourcePromptEngineerInitialization:
    """Test ResourcePromptEngineer initialization (Phase 1)."""
    
    def test_initialization_with_resource_component(self):
        """Test 1.1: Initialization with resource component."""
        resource = MockResourceWithTool()
        engineer = ResourcePromptEngineer(resource)
        
        assert engineer._component == resource
        assert engineer._codec == CSXMLCodec
        assert engineer._force_generate is False
        assert engineer._check_conflicts is False
    
    def test_initialization_with_custom_codec(self):
        """Test 1.2: Initialization with custom codec."""
        resource = MockResourceWithTool()
        engineer = ResourcePromptEngineer(resource, codec=KLXMLCodec)
        
        assert engineer._component == resource
        assert engineer._codec == KLXMLCodec
    
    def test_initialization_with_storage(self):
        """Test 1.3: Initialization with storage."""
        resource = MockResourceWithTool()
        mock_storage = Mock(spec=AbstractStorage)
        engineer = ResourcePromptEngineer(resource, storage=mock_storage)
        
        assert engineer._component == resource
        assert engineer._storage == mock_storage
    
    def test_initialization_with_force_generate(self):
        """Test initialization with force_generate flag."""
        resource = MockResourceWithTool()
        engineer = ResourcePromptEngineer(resource, force_generate=True)
        
        assert engineer._force_generate is True
    
    def test_initialization_with_check_conflicts(self):
        """Test initialization with check_conflicts flag."""
        resource = MockResourceWithTool()
        engineer = ResourcePromptEngineer(resource, check_conflicts=True)
        
        assert engineer._check_conflicts is True


class TestResourcePromptEngineerConstructPrompt:
    """Test ResourcePromptEngineer.construct_prompt() (Phase 2)."""
    
    def test_construct_prompt_with_single_tool_method(self):
        """Test 2.1: construct_prompt with single @tool_use method."""
        resource = MockResourceWithTool()
        engineer = ResourcePromptEngineer(resource)
        
        prompt = engineer.construct_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should contain formatted method using CSXMLCodec format
        assert "# MockResourceWithTool:test_method" in prompt or "test_method" in prompt
        assert "Test method with one parameter" in prompt or "param1" in prompt
    
    def test_construct_prompt_with_multiple_tool_methods(self):
        """Test 2.2: construct_prompt with multiple @tool_use methods."""
        resource = MockResourceMultipleTools()
        engineer = ResourcePromptEngineer(resource)
        
        prompt = engineer.construct_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should contain all three methods
        assert "method_one" in prompt or "method_one" in prompt.lower()
        assert "method_two" in prompt or "method_two" in prompt.lower()
        assert "method_three" in prompt or "method_three" in prompt.lower()
    
    def test_construct_prompt_with_no_tool_methods(self):
        """Test 2.3: construct_prompt with no @tool_use methods."""
        resource = MockResourceWithoutTool()
        engineer = ResourcePromptEngineer(resource)
        
        prompt = engineer.construct_prompt()
        
        assert isinstance(prompt, str)
        # Should return resource description or empty string
        # (since no tool methods exist)
    
    def test_construct_prompt_with_klxml_codec(self):
        """Test 2.4: construct_prompt with KLXMLCodec."""
        resource = MockResourceWithTool()
        engineer = ResourcePromptEngineer(resource, codec=KLXMLCodec)
        
        prompt = engineer.construct_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should use KLXML format (not CSXML function_call format)
        # KLXML format uses <Class:method> tags, not <function_call><invoke>
        assert "<MockResourceWithTool:test_method>" in prompt or "MockResourceWithTool:test_method" in prompt
    
    def test_construct_prompt_includes_resource_description(self):
        """Test 2.5: construct_prompt includes resource description."""
        class ResourceWithDescription(BaseResource):
            """This is a test resource description."""
            
            def __init__(self, **kwargs):
                super().__init__(resource_type="test_desc", auto_register=False, **kwargs)
            
            @tool_use
            def test_method(self) -> DictParams:
                """Test method."""
                return {}
        
        resource = ResourceWithDescription()
        engineer = ResourcePromptEngineer(resource)
        
        prompt = engineer.construct_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should include resource description from docstring
        assert "test resource description" in prompt.lower() or "ResourceWithDescription" in prompt


class TestResourcePromptEngineerCheckConflicts:
    """Test ResourcePromptEngineer.check_conflicts() (Phase 3)."""
    
    def test_check_conflicts_with_unique_method_names(self):
        """Test 3.1: check_conflicts with unique method names."""
        resource = MockResourceMultipleTools()
        engineer = ResourcePromptEngineer(resource)
        
        result = engineer.check_conflicts()
        
        assert isinstance(result, bool)
        assert result is False  # No conflicts expected
    
    def test_check_conflicts_returns_bool(self):
        """Test 3.2: check_conflicts always returns boolean."""
        resource = MockResourceWithTool()
        engineer = ResourcePromptEngineer(resource)
        
        result = engineer.check_conflicts()
        
        assert isinstance(result, bool)


class TestResourcePromptEngineerIntegration:
    """Test ResourcePromptEngineer integration with real resources (Phase 4)."""
    
    @pytest.fixture
    def create_file_resource(self):
        """Create a CreateFileResource instance for testing."""
        import os
        import sys
        examples_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", 
            "examples", "agents", "financial-analysis", "resources"
        )
        if os.path.exists(examples_path):
            sys.path.insert(0, examples_path)
            try:
                from create_file_resource import CreateFileResource
                return CreateFileResource(workspace_root='/tmp', auto_register=False)
            except ImportError:
                pytest.skip("CreateFileResource not available")
        else:
            pytest.skip("Examples path not found")
    
    def test_with_real_create_file_resource(self, create_file_resource):
        """Test 4.1: Integration with real CreateFileResource."""
        engineer = ResourcePromptEngineer(create_file_resource)
        
        prompt = engineer.construct_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should contain CreateFileResource method
        assert "CreateFileResource" in prompt or "create" in prompt.lower()
        # Should contain method signature
        assert "relative_workspace_path" in prompt
    
    def test_codec_integration_csxml(self):
        """Test 4.2a: Verify CSXMLCodec integration."""
        resource = MockResourceWithTool()
        engineer = ResourcePromptEngineer(resource, codec=CSXMLCodec)
        
        prompt = engineer.construct_prompt()
        
        # CSXMLCodec should produce function_call format
        assert "<function_call>" in prompt or "# MockResourceWithTool:test_method" in prompt
    
    def test_codec_integration_klxml(self):
        """Test 4.2b: Verify KLXMLCodec integration."""
        resource = MockResourceWithTool()
        engineer = ResourcePromptEngineer(resource, codec=KLXMLCodec)
        
        prompt = engineer.construct_prompt()
        
        # KLXMLCodec should produce <Class:method> format
        assert "<MockResourceWithTool:test_method>" in prompt or "MockResourceWithTool:test_method" in prompt

