"""
Unit tests for the BaseResource class.

This module tests the core BaseResource class functionality including
initialization, protocol compliance, and resource management.
"""

from unittest.mock import Mock

from adana.common.protocols import DictParams, Identifiable, Notifiable, ResourceProtocol
from adana.core.resource import BaseResource


class TestBaseResource:
    """Test BaseResource class functionality."""

    def test_init_defaults(self):
        """Test BaseResource initialization with default values."""
        resource = BaseResource()

        # Test basic properties
        assert resource.resource_type == "BaseResource"  # Uses class name as default
        assert isinstance(resource.object_id, str)
        assert len(resource.object_id) > 0

    def test_init_with_resource_type(self):
        """Test BaseResource initialization with custom resource type."""
        resource = BaseResource(resource_type="custom_database")

        assert resource.resource_type == "custom_database"
        assert isinstance(resource.object_id, str)

    def test_object_id_auto_generation(self):
        """Test BaseResource automatically generates object_id."""
        resource = BaseResource()

        assert isinstance(resource.object_id, str)
        assert len(resource.object_id) > 0
        assert resource.resource_type == "BaseResource"

    def test_init_with_resource_type_only(self):
        """Test BaseResource initialization with resource_type only."""
        resource = BaseResource(resource_type="test_resource")

        assert resource.resource_type == "test_resource"
        assert isinstance(resource.object_id, str)

    def test_base_resource_notification_integration(self):
        """Test BaseResource notification functionality."""
        resource = BaseResource(resource_type="test_resource")

        # Test that resource inherits notification functionality from BaseWR
        assert hasattr(resource, "_notifiables")
        assert hasattr(resource, "broadcast")
        assert hasattr(resource, "add_notifier")
        assert hasattr(resource, "remove_notifiable")

        # Test notification sending
        mock_notifiable = Mock(spec=Notifiable)
        resource.add_notifier(mock_notifiable)

        test_message = {"type": "resource_test", "content": "resource notification"}
        resource.broadcast(test_message)

        mock_notifiable.notify.assert_called_once_with(resource, test_message)

    def test_object_id_generation(self):
        """Test that object_id is generated when not provided."""
        resource1 = BaseResource()
        resource2 = BaseResource()

        # Each resource should have unique object_ids
        assert resource1.object_id != resource2.object_id
        assert isinstance(resource1.object_id, str)
        assert isinstance(resource2.object_id, str)

    def test_protocol_compliance(self):
        """Test that BaseResource implements required protocols."""
        resource = BaseResource()

        # Test BaseResourceProtocol compliance
        assert isinstance(resource, ResourceProtocol)

        # Test Identifiable compliance
        assert isinstance(resource, Identifiable)

        # Test required methods exist
        assert hasattr(resource, "query")
        assert hasattr(resource, "object_id")
        assert hasattr(resource, "public_description")

    def test_public_description(self):
        """Test public_description property."""
        resource = BaseResource()

        # Should have public_description property
        description = resource.public_description
        assert isinstance(description, str)
        assert len(description) > 0

    def test_query_method(self):
        """Test query method functionality."""
        resource = BaseResource()

        # Test basic query
        result = resource.query()
        assert isinstance(result, dict)
        assert result == {}  # Default implementation returns empty dict

        # Test query with parameters
        result = resource.query(param1="value1", param2="value2")
        assert isinstance(result, dict)
        assert result == {}  # Default implementation ignores parameters

    def test_resource_uniqueness(self):
        """Test that each resource has unique object_ids."""
        resource1 = BaseResource()
        resource2 = BaseResource()
        resource3 = BaseResource()

        # Each resource should have unique object_ids
        assert resource1.object_id != resource2.object_id
        assert resource1.object_id != resource3.object_id
        assert resource2.object_id != resource3.object_id

    def test_resource_string_representation(self):
        """Test resource string representation."""
        resource = BaseResource(resource_type="test_resource")

        # Should have meaningful string representation
        str_repr = str(resource)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    def test_resource_with_different_types(self):
        """Test resources with different types."""
        db_resource = BaseResource(resource_type="database")
        api_resource = BaseResource(resource_type="api")

        assert db_resource.resource_type == "database"
        assert api_resource.resource_type == "api"
        assert db_resource.resource_type != api_resource.resource_type

    def test_object_id_uniqueness(self):
        """Test that object_ids are unique across resources."""
        resources = [BaseResource() for _ in range(10)]
        object_ids = [r.object_id for r in resources]

        # All object_ids should be unique
        assert len(set(object_ids)) == 10

    def test_resource_with_kwargs(self):
        """Test resource initialization with additional kwargs."""
        resource = BaseResource(resource_type="test_resource", custom_param="custom_value")

        assert resource.resource_type == "test_resource"
        assert isinstance(resource.object_id, str)


class TestBaseResourceIntegration:
    """Test BaseResource integration with other components."""

    def test_resource_as_protocol(self):
        """Test that BaseResource can be used as BaseResourceProtocol."""
        resource = BaseResource()

        # Should be usable as BaseResourceProtocol
        def use_resource(r: ResourceProtocol) -> DictParams:
            return r.query(test_param="value")

        result = use_resource(resource)
        assert isinstance(result, dict)

    def test_resource_with_tool_methods(self):
        """Test resource with tool-usable methods."""
        from adana.common.protocols.war import tool_use

        class TestBaseResource(BaseResource):
            @tool_use
            def get_data(self, table: str) -> DictParams:
                return {"table": table, "data": "test_data"}

            def regular_method(self) -> str:
                return "regular"

        resource = TestBaseResource()

        # Test tool-usable method
        result = resource.get_data("users")
        assert result == {"table": "users", "data": "test_data"}

        # Test regular method
        result = resource.regular_method()
        assert result == "regular"

        # Test that tool_use decorator works
        assert hasattr(resource.get_data, "_is_tool_use")
        assert resource.get_data._is_tool_use is True
        assert not hasattr(resource.regular_method, "_is_tool_use")


class TestPingResource:
    """Test PingResource class functionality."""

    def test_ping_resource_initialization(self):
        """Test PingResource initialization."""
        from adana.lib.resources import PingResource

        resource = PingResource()

        # Should inherit from BaseResource
        assert hasattr(resource, "resource_type")
        assert hasattr(resource, "object_id")
        assert hasattr(resource, "query")

    def test_ping_resource_query_default(self):
        """Test PingResource query with default message."""
        from adana.lib.resources import PingResource

        resource = PingResource()
        result = resource.query()

        assert isinstance(result, dict)
        assert "message" in result
        assert result["message"] == "Pong"

    def test_ping_resource_query_custom_message(self):
        """Test PingResource query with custom message."""
        from adana.lib.resources import PingResource

        resource = PingResource()
        result = resource.query(message="Hello")

        assert isinstance(result, dict)
        assert "message" in result
        assert result["message"] == "Hello"

    def test_ping_resource_query_with_kwargs(self):
        """Test PingResource query with kwargs."""
        from adana.lib.resources import PingResource

        resource = PingResource()
        result = resource.query(message="Test message")

        assert isinstance(result, dict)
        assert "message" in result
        assert result["message"] == "Test message"

    def test_ping_resource_notification_integration(self):
        """Test PingResource notification functionality."""
        from adana.lib.resources import PingResource

        resource = PingResource()

        # Test that resource inherits notification functionality
        assert hasattr(resource, "_notifiables")
        assert hasattr(resource, "broadcast")
        assert hasattr(resource, "add_notifier")
        assert hasattr(resource, "remove_notifiable")

        # Test notification sending
        mock_notifiable = Mock(spec=Notifiable)
        resource.add_notifier(mock_notifiable)

        test_message = {"type": "ping_test", "content": "ping notification"}
        resource.broadcast(test_message)

        mock_notifiable.notify.assert_called_once_with(resource, test_message)

    def test_ping_resource_query_with_notifications(self):
        """Test PingResource query with notification support."""
        from adana.lib.resources import PingResource

        resource = PingResource()

        # Add a notifiable to track query calls
        mock_notifiable = Mock(spec=Notifiable)
        resource.add_notifier(mock_notifiable)

        # Perform a query
        result = resource.query(message="Test ping")

        # Should return expected result
        assert result["message"] == "Test ping"

        # Note: The current implementation doesn't send notifications during query
        # This test documents the current behavior and can be updated if
        # notifications are added to the query method in the future


class TestBaseResourceEdgeCases:
    """Test BaseResource edge cases and error handling."""

    def test_resource_auto_id_generation(self):
        """Test resource automatically generates object_id."""
        resource = BaseResource()
        assert isinstance(resource.object_id, str)
        assert len(resource.object_id) > 0

    def test_resource_with_very_long_type(self):
        """Test resource with very long resource_type."""
        long_type = "a" * 1000
        resource = BaseResource(resource_type=long_type)
        assert resource.resource_type == long_type

    def test_resource_with_special_characters_type(self):
        """Test resource with special characters in type."""
        special_type = "resource-with_special.chars@123"
        resource = BaseResource(resource_type=special_type)
        assert resource.resource_type == special_type
