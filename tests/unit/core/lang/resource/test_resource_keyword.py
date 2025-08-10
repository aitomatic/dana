"""
Tests for Resource Keyword Implementation

This module tests the resource keyword functionality including:
- Grammar parsing
- AST node creation
- Resource blueprint creation
- Agent-only access validation
- Resource registry operations
"""

import pytest
from unittest.mock import Mock, patch

from dana.core.resource import (
    BaseResource,
    ResourceState,
    ResourceHandle,
    ResourceRegistry,
    ResourceError,
    MCPResource,
    RAGResource,
)
from dana.core.resource.context_integration import (
    ResourceContextIntegrator,
    AgentAccessError,
    get_resource_integrator,
)
from dana.core.lang.ast import (
    ResourceDefinition,
    ResourceField,
    ResourceMethod,
    TypeHint,
)


class TestBaseResource:
    """Test the base resource functionality."""

    def test_resource_creation(self):
        """Test creating a basic resource."""
        resource = BaseResource(kind="test", name="test_resource", description="A test resource")

        assert resource.kind == "test"
        assert resource.name == "test_resource"
        assert resource.description == "A test resource"
        assert resource.state == ResourceState.CREATED
        assert not resource.is_running()

    def test_resource_lifecycle(self):
        """Test resource lifecycle management."""
        resource = BaseResource(kind="test", name="test_resource")

        # Test start
        assert resource.start()
        assert resource.is_running()
        assert resource.state == ResourceState.RUNNING

        # Test suspend
        assert resource.suspend()
        assert resource.state == ResourceState.SUSPENDED
        assert not resource.is_running()

        # Test resume
        assert resource.resume()
        assert resource.is_running()

        # Test stop
        assert resource.stop()
        assert resource.state == ResourceState.TERMINATED
        assert not resource.is_running()

    def test_resource_metadata(self):
        """Test resource metadata generation."""
        resource = BaseResource(
            kind="test",
            name="test_resource",
            version="2.0.0",
            domain="testing",
            tags=["unit", "test"],
            capabilities=["test", "validate"],
            permissions=["read"],
        )

        metadata = resource.get_metadata()
        assert metadata["kind"] == "test"
        assert metadata["name"] == "test_resource"
        assert metadata["version"] == "2.0.0"
        assert metadata["domain"] == "testing"
        assert metadata["tags"] == ["unit", "test"]
        assert metadata["capabilities"] == ["test", "validate"]
        assert metadata["permissions"] == ["read"]


class TestResourceHandle:
    """Test resource handle functionality for transfers."""

    def test_handle_creation(self):
        """Test creating a resource handle."""
        handle = ResourceHandle(
            kind="mcp",
            name="test_mcp",
            version="1.0.0",
            description="Test MCP resource",
            domain="general",
            capabilities=["query", "call_tool"],
        )

        assert handle.kind == "mcp"
        assert handle.name == "test_mcp"
        assert handle.validate()

    def test_handle_serialization(self):
        """Test handle serialization to/from dict."""
        original = ResourceHandle(
            kind="rag",
            name="test_rag",
            version="1.0.0",
            description="Test RAG",
            domain="testing",
            tags=["test"],
            config={"sources": ["test.pdf"]},
        )

        # Serialize
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data["kind"] == "rag"
        assert data["config"]["sources"] == ["test.pdf"]

        # Deserialize
        recreated = ResourceHandle.from_dict(data)
        assert recreated.kind == original.kind
        assert recreated.name == original.name
        assert recreated.config == original.config

    def test_handle_compatibility(self):
        """Test handle compatibility checking."""
        handle = ResourceHandle(kind="mcp", name="test", version="1.0.0", description="Test handle", domain="general")

        assert handle.is_compatible_with("mcp")
        assert not handle.is_compatible_with("rag")


class TestResourceRegistry:
    """Test the resource registry functionality."""

    def test_blueprint_registration(self):
        """Test registering resource blueprints."""
        registry = ResourceRegistry()

        registry.register_blueprint("test", BaseResource)
        assert "test" in registry._blueprints
        assert registry._blueprints["test"] == BaseResource

    def test_resource_creation(self):
        """Test creating resources through the registry."""
        registry = ResourceRegistry()
        registry.register_blueprint("test", BaseResource)

        resource = registry.create_resource("test", "test_resource", "test_agent")

        assert resource.name == "test_resource"
        assert resource.kind == "test"
        assert resource.owner_agent == "test_agent"
        assert registry.get_resource("test_resource") is resource

    def test_resource_transfer(self):
        """Test transferring resources between agents."""
        registry = ResourceRegistry()
        registry.register_blueprint("test", BaseResource)

        # Create resource owned by agent1
        resource = registry.create_resource("test", "test_resource", "agent1")
        assert resource.owner_agent == "agent1"

        # Transfer to agent2
        success = registry.transfer_resource("test_resource", "agent1", "agent2")
        assert success
        assert resource.owner_agent == "agent2"

        # Verify agent tracking
        agent1_resources = registry.list_resources("agent1")
        agent2_resources = registry.list_resources("agent2")
        assert len(agent1_resources) == 0
        assert len(agent2_resources) == 1
        assert agent2_resources[0] is resource

    def test_handle_creation_and_reconstruction(self):
        """Test creating handles and reconstructing resources."""
        registry = ResourceRegistry()
        registry.register_blueprint("test", BaseResource)

        # Create original resource
        original = registry.create_resource("test", "test_resource", "agent1", description="Test resource", tags=["test"])

        # Create handle
        handle = registry.create_handle("test_resource")
        assert handle.kind == "test"
        assert handle.name == "test_resource"
        assert handle.source_agent == "agent1"

        # Reconstruct from handle with different name to avoid conflict
        handle.name = "test_resource_copy"
        reconstructed = registry.create_from_handle(handle, "agent2")
        assert reconstructed.kind == original.kind
        assert reconstructed.name == "test_resource_copy"
        assert reconstructed.owner_agent == "agent2"  # Different agent

    def test_agent_cleanup(self):
        """Test cleaning up agent resources."""
        registry = ResourceRegistry()
        registry.register_blueprint("test", BaseResource)

        # Create resources for agent
        resource1 = registry.create_resource("test", "resource1", "agent1")
        resource2 = registry.create_resource("test", "resource2", "agent1")

        # Verify created
        agent_resources = registry.list_resources("agent1")
        assert len(agent_resources) == 2

        # Cleanup agent
        registry.cleanup_agent_resources("agent1")

        # Verify cleanup
        agent_resources = registry.list_resources("agent1")
        assert len(agent_resources) == 0
        assert registry.get_resource("resource1") is None
        assert registry.get_resource("resource2") is None


class TestAgentOnlyAccess:
    """Test agent-only access validation."""

    def test_agent_context_validation(self):
        """Test that resources can only be accessed in agent context."""
        integrator = ResourceContextIntegrator()

        # No agent context - should fail
        with pytest.raises(AgentAccessError):
            integrator.validate_agent_access()

        # Set agent context - should succeed
        integrator.set_agent_context("test_agent")
        agent_name = integrator.validate_agent_access()
        assert agent_name == "test_agent"

        # Clear context - should fail again
        integrator.clear_agent_context()
        with pytest.raises(AgentAccessError):
            integrator.validate_agent_access()

    def test_resource_creation_with_agent_validation(self):
        """Test creating resources requires agent context."""
        integrator = ResourceContextIntegrator()
        mock_sandbox = Mock()

        # No agent context - should fail
        with pytest.raises(AgentAccessError):
            integrator.create_resource("mcp", "test_mcp", mock_sandbox)

        # Set agent context - should succeed
        integrator.set_agent_context("test_agent")
        resource = integrator.create_resource("mcp", "test_mcp", mock_sandbox)

        assert isinstance(resource, MCPResource)
        assert resource.owner_agent == "test_agent"
        mock_sandbox.set_resource.assert_called_once_with("test_mcp", resource)

    def test_resource_method_invocation_validation(self):
        """Test that resource methods validate agent access."""
        integrator = ResourceContextIntegrator()
        mock_sandbox = Mock()

        # Create resource
        integrator.set_agent_context("agent1")
        resource = integrator.create_resource("mcp", "test_mcp", mock_sandbox)
        mock_sandbox.get_resource.return_value = resource

        # Same agent can invoke methods
        result = integrator.invoke_resource_method("test_mcp", "initialize", mock_sandbox)
        assert result is not None  # initialize returns something

        # Different agent cannot invoke methods
        integrator.set_agent_context("agent2")
        with pytest.raises(AgentAccessError):
            integrator.invoke_resource_method("test_mcp", "initialize", mock_sandbox)


class TestStandardResourceBlueprints:
    """Test the standard resource blueprint implementations."""

    def test_mcp_resource(self):
        """Test MCP resource blueprint."""
        mcp = MCPResource(name="test_mcp", endpoint="http://localhost:8080", auth={"token": "test"})

        assert mcp.kind == "mcp"
        assert mcp.endpoint == "http://localhost:8080"
        assert mcp.auth["token"] == "test"

        # Test methods exist
        assert hasattr(mcp, "list_tools")
        assert hasattr(mcp, "call_tool")
        assert callable(mcp.list_tools)
        assert callable(mcp.call_tool)

    def test_rag_resource(self):
        """Test RAG resource blueprint."""
        rag = RAGResource(name="test_rag", sources=["doc1.pdf", "doc2.txt"], chunk_size=512, reranking=True)

        assert rag.kind == "rag"
        assert rag.sources == ["doc1.pdf", "doc2.txt"]
        assert rag.chunk_size == 512
        assert rag.reranking is True

        # Test query method exists
        assert hasattr(rag, "query")
        assert callable(rag.query)


class TestAST:
    """Test AST nodes for resource definitions."""

    def test_resource_definition(self):
        """Test ResourceDefinition AST node."""
        definition = ResourceDefinition(name="MyMCP", parent_name="MCPResource", fields=[], methods=[])

        assert definition.name == "MyMCP"
        assert definition.parent_name == "MCPResource"

    def test_resource_field(self):
        """Test ResourceField AST node."""
        field = ResourceField(name="timeout", type_hint=TypeHint(name="int"), default_value=None, comment="Request timeout in seconds")

        assert field.name == "timeout"
        assert field.type_hint.name == "int"
        assert field.comment == "Request timeout in seconds"


if __name__ == "__main__":
    pytest.main([__file__])
