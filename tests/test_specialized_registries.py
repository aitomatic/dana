"""
Tests for specialized registries (AgentRegistry and ResourceRegistry).
"""

from dana.core.builtin_types.struct_system import StructInstance
from dana.registry import AGENT_REGISTRY, RESOURCE_REGISTRY


def create_mock_struct_instance(name: str) -> StructInstance:
    """Create a mock StructInstance for testing."""
    instance = StructInstance.__new__(StructInstance)
    instance.instance_id = f"test_{name}_{id(instance)}"
    return instance


class TestAgentRegistry:
    """Test AgentRegistry specialized functionality."""

    def setup_method(self):
        """Clear registries before each test."""
        AGENT_REGISTRY.clear()

    def test_track_agent_with_metadata(self):
        """Test tracking an agent with specialized metadata."""
        agent = create_mock_struct_instance("test_agent")

        agent_id = AGENT_REGISTRY.track_agent(agent, name="Test Agent", role="researcher", capabilities=["research", "analysis"])

        assert AGENT_REGISTRY.get_agent_role(agent_id) == "researcher"
        assert AGENT_REGISTRY.get_agent_capabilities(agent_id) == ["research", "analysis"]
        assert AGENT_REGISTRY.get_agent_status(agent_id) == "active"

    def test_get_agents_by_role(self):
        """Test filtering agents by role."""
        agent1 = create_mock_struct_instance("agent1")
        agent2 = create_mock_struct_instance("agent2")

        AGENT_REGISTRY.track_agent(agent1, role="researcher")
        AGENT_REGISTRY.track_agent(agent2, role="coder")

        researchers = AGENT_REGISTRY.get_agents_by_role("researcher")
        assert len(researchers) == 1

        coders = AGENT_REGISTRY.get_agents_by_role("coder")
        assert len(coders) == 1

    def test_get_active_agents(self):
        """Test getting active agents."""
        agent1 = create_mock_struct_instance("agent1")
        agent2 = create_mock_struct_instance("agent2")

        agent1_id = AGENT_REGISTRY.track_agent(agent1)
        _ = AGENT_REGISTRY.track_agent(agent2)  # agent2_id unused

        active_agents = AGENT_REGISTRY.get_active_agents()
        assert len(active_agents) == 2

        # Set one agent to busy
        AGENT_REGISTRY.set_agent_status(agent1_id, "busy")
        active_agents = AGENT_REGISTRY.get_active_agents()
        assert len(active_agents) == 1

    def test_untrack_agent(self):
        """Test untracking an agent."""
        agent = create_mock_struct_instance("test_agent")
        agent_id = AGENT_REGISTRY.track_agent(agent, role="researcher")

        assert AGENT_REGISTRY.get_agent_role(agent_id) == "researcher"

        # Untrack the agent
        assert AGENT_REGISTRY.untrack_agent(agent_id) is True
        assert AGENT_REGISTRY.get_agent_role(agent_id) is None


class TestResourceRegistry:
    """Test ResourceRegistry specialized functionality."""

    def setup_method(self):
        """Clear registries before each test."""
        RESOURCE_REGISTRY.clear()

    def test_track_resource_with_metadata(self):
        """Test tracking a resource with specialized metadata."""
        resource = create_mock_struct_instance("test_resource")

        resource_id = RESOURCE_REGISTRY.track_resource(
            resource, name="Test Resource", resource_type="database", provider="AWS", permissions=["read", "write"]
        )

        assert RESOURCE_REGISTRY.get_resource_type(resource_id) == "database"
        assert RESOURCE_REGISTRY.get_resource_provider(resource_id) == "AWS"
        assert RESOURCE_REGISTRY.get_resource_permissions(resource_id) == ["read", "write"]
        assert RESOURCE_REGISTRY.get_resource_status(resource_id) == "available"

    def test_get_resources_by_type(self):
        """Test filtering resources by type."""
        resource1 = create_mock_struct_instance("resource1")
        resource2 = create_mock_struct_instance("resource2")

        RESOURCE_REGISTRY.track_resource(resource1, resource_type="database")
        RESOURCE_REGISTRY.track_resource(resource2, resource_type="api")

        databases = RESOURCE_REGISTRY.get_resources_by_type("database")
        assert len(databases) == 1

        apis = RESOURCE_REGISTRY.get_resources_by_type("api")
        assert len(apis) == 1

    def test_get_resources_by_provider(self):
        """Test filtering resources by provider."""
        resource1 = create_mock_struct_instance("resource1")
        resource2 = create_mock_struct_instance("resource2")

        RESOURCE_REGISTRY.track_resource(resource1, provider="AWS")
        RESOURCE_REGISTRY.track_resource(resource2, provider="Google")

        aws_resources = RESOURCE_REGISTRY.get_resources_by_provider("AWS")
        assert len(aws_resources) == 1

        google_resources = RESOURCE_REGISTRY.get_resources_by_provider("Google")
        assert len(google_resources) == 1

    def test_get_available_resources(self):
        """Test getting available resources."""
        resource1 = create_mock_struct_instance("resource1")
        resource2 = create_mock_struct_instance("resource2")

        resource1_id = RESOURCE_REGISTRY.track_resource(resource1)
        _ = RESOURCE_REGISTRY.track_resource(resource2)  # resource2_id unused

        available_resources = RESOURCE_REGISTRY.get_available_resources()
        assert len(available_resources) == 2

        # Set one resource to maintenance
        RESOURCE_REGISTRY.set_resource_status(resource1_id, "maintenance")
        available_resources = RESOURCE_REGISTRY.get_available_resources()
        assert len(available_resources) == 1

    def test_add_remove_permissions(self):
        """Test adding and removing resource permissions."""
        resource = create_mock_struct_instance("test_resource")
        resource_id = RESOURCE_REGISTRY.track_resource(resource, permissions=["read"])

        # Add permission
        RESOURCE_REGISTRY.add_resource_permission(resource_id, "write")
        permissions = RESOURCE_REGISTRY.get_resource_permissions(resource_id)
        assert "read" in permissions
        assert "write" in permissions

        # Remove permission
        RESOURCE_REGISTRY.remove_resource_permission(resource_id, "read")
        permissions = RESOURCE_REGISTRY.get_resource_permissions(resource_id)
        assert "read" not in permissions
        assert "write" in permissions

    def test_untrack_resource(self):
        """Test untracking a resource."""
        resource = create_mock_struct_instance("test_resource")
        resource_id = RESOURCE_REGISTRY.track_resource(resource, resource_type="database", provider="AWS")

        assert RESOURCE_REGISTRY.get_resource_type(resource_id) == "database"
        assert RESOURCE_REGISTRY.get_resource_provider(resource_id) == "AWS"

        # Untrack the resource
        assert RESOURCE_REGISTRY.untrack_resource(resource_id) is True
        assert RESOURCE_REGISTRY.get_resource_type(resource_id) is None
        assert RESOURCE_REGISTRY.get_resource_provider(resource_id) is None


class TestSpecializedRegistryInheritance:
    """Test that specialized registries properly inherit from StructRegistry."""

    def test_agent_registry_inheritance(self):
        """Test that AgentRegistry inherits StructRegistry functionality."""
        agent = create_mock_struct_instance("test_agent")

        # Test basic StructRegistry functionality
        agent_id = AGENT_REGISTRY.track_instance(agent, "Test Agent")
        assert AGENT_REGISTRY.get_instance(agent_id) is agent
        assert AGENT_REGISTRY.count() == 1

        # Test specialized AgentRegistry functionality
        assert AGENT_REGISTRY.get_agent_status(agent_id) == "unknown"  # Not set via track_instance

    def test_resource_registry_inheritance(self):
        """Test that ResourceRegistry inherits StructRegistry functionality."""
        resource = create_mock_struct_instance("test_resource")

        # Test basic StructRegistry functionality
        resource_id = RESOURCE_REGISTRY.track_resource(resource, "Test Resource")
        assert RESOURCE_REGISTRY.get_instance(resource_id) is resource
        assert RESOURCE_REGISTRY.count() == 1

        # Test specialized ResourceRegistry functionality
        assert RESOURCE_REGISTRY.get_resource_status(resource_id) == "available"  # Set via track_resource
