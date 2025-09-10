"""
Tests for Resource Keyword Implementation

This module tests the resource keyword functionality including:
- Grammar parsing
- AST node creation
- Resource type creation
- Resource registry operations
"""

import pytest

from dana.core.lang.ast import (
    ResourceDefinition,
    ResourceField,
    TypeHint,
)
from dana.core.resource import (
    ResourceInstance,
    ResourceType,
    ResourceTypeRegistry,
)


class TestResourceType:
    """Test the resource type functionality."""

    def test_resource_type_creation(self):
        """Test creating a basic resource type."""
        resource_type = ResourceType(
            name="TestResource",
            fields={"name": "str", "kind": "str"},
            field_order=["name", "kind"],
            field_defaults={"kind": "test"},
        )

        assert resource_type.name == "TestResource"
        assert resource_type.fields["name"] == "str"
        assert resource_type.fields["kind"] == "str"
        assert resource_type.field_order == ["state", "name", "kind"]
        assert resource_type.field_defaults["kind"] == "test"
        assert resource_type.field_defaults["state"] == "CREATED"

    def test_resource_type_composition(self):
        """Test resource type composition without inheritance."""
        # Create independent resource types
        extended_type = ResourceType(
            name="ExtendedResource",
            fields={"name": "str", "kind": "str", "extra_field": "int"},
            field_order=["name", "kind", "extra_field"],
            field_defaults={"kind": "extended", "extra_field": 42},
        )

        # Check that they are independent (no inheritance)
        assert "name" in extended_type.fields
        assert "kind" in extended_type.fields
        assert "extra_field" in extended_type.fields
        assert extended_type.field_order == ["state", "name", "kind", "extra_field"]
        assert extended_type.field_defaults["kind"] == "extended"
        assert extended_type.field_defaults["extra_field"] == 42
        assert extended_type.field_defaults["state"] == "CREATED"


class TestResourceInstance:
    """Test the resource instance functionality."""

    def test_resource_instance_creation(self):
        """Test creating a resource instance."""
        resource_type = ResourceType(
            name="TestResource",
            fields={"name": "str", "kind": "str"},
            field_order=["name", "kind"],
            field_defaults={"kind": "test"},
        )

        instance = ResourceInstance(resource_type, {"name": "test_instance"})

        assert instance.name == "test_instance"
        assert instance.kind == "test"  # Default value
        assert instance.state == "INITIALIZED"  # Resource is automatically initialized during creation

    def test_resource_lifecycle(self):
        """Test resource lifecycle management."""
        resource_type = ResourceType(
            name="TestResource",
            fields={"name": "str"},
            field_order=["name"],
        )

        instance = ResourceInstance(resource_type, {"name": "test_resource"})

        # Test initialize
        assert instance.initialize()
        assert instance.state == "INITIALIZED"

        # Test start
        assert instance.start()
        assert instance.state == "RUNNING"
        assert instance.is_running()

        # Test stop
        assert instance.stop()
        assert instance.state == "TERMINATED"
        assert not instance.is_running()

        # Test cleanup
        assert instance.cleanup()
        assert instance.state == "TERMINATED"

    def test_composition_and_delegation(self):
        """Test composition and delegation in resource instances."""
        # Create resource type
        resource_type = ResourceType(
            name="ComposedResource",
            fields={"name": "str"},
            field_order=["name"],
        )

        # Create instance
        instance = ResourceInstance(resource_type, {"name": "test"})

        # Create a backend object
        class Backend:
            def process(self):
                return "processed"

            def compute(self, value):
                return value * 2

        backend = Backend()
        instance.set_backend(backend)

        # Test backend delegation
        assert instance.has_method("process")
        assert instance.call_method("process") == "processed"
        assert instance.call_method("compute", 5) == 10

        # Create a delegate object
        class Logger:
            def log_message(self, message):
                return f"logged: {message}"

        logger = Logger()
        instance.add_delegate("logger", logger)

        # Test delegate methods
        assert instance.has_method("log_message")
        assert instance.call_method("log_message", "test message") == "logged: test message"

        # Test delegate management
        assert instance.get_delegate("logger") == logger
        instance.remove_delegate("logger")
        assert instance.get_delegate("logger") is None
        assert not instance.has_method("log_message")


class TestResourceTypeRegistry:
    """Test the resource type registry functionality."""

    def setup_method(self):
        """Clear registry before each test."""
        ResourceTypeRegistry.clear()

    def test_resource_type_registration(self):
        """Test registering resource types."""
        resource_type = ResourceType(
            name="TestResource",
            fields={"name": "str"},
            field_order=["name"],
        )

        ResourceTypeRegistry.register_resource(resource_type)
        assert ResourceTypeRegistry.exists("TestResource")
        assert ResourceTypeRegistry.get_resource_type("TestResource") == resource_type

    def test_resource_instance_creation(self):
        """Test creating resource instances through the registry."""
        resource_type = ResourceType(
            name="TestResource",
            fields={"name": "str", "kind": "str"},
            field_order=["name", "kind"],
            field_defaults={"kind": "test"},
        )

        ResourceTypeRegistry.register_resource(resource_type)

        instance = ResourceTypeRegistry.create_resource_instance("TestResource", {"name": "test_instance"})

        assert instance.name == "test_instance"
        assert instance.kind == "test"
        assert isinstance(instance, ResourceInstance)

    def test_resource_composition_queries(self):
        """Test resource type queries for composition-based resources."""
        # Create independent resource types
        base_type = ResourceType(name="BaseResource", fields={"id": "str"}, field_order=["id"])
        extended_type = ResourceType(name="ExtendedResource", fields={"id": "str", "name": "str"}, field_order=["id", "name"])
        specialized_type = ResourceType(
            name="SpecializedResource", fields={"id": "str", "name": "str", "value": "int"}, field_order=["id", "name", "value"]
        )

        ResourceTypeRegistry.register_resource(base_type)
        ResourceTypeRegistry.register_resource(extended_type)
        ResourceTypeRegistry.register_resource(specialized_type)

        # Test that types are registered independently
        assert ResourceTypeRegistry.exists("BaseResource")
        assert ResourceTypeRegistry.exists("ExtendedResource")
        assert ResourceTypeRegistry.exists("SpecializedResource")

        # Test getting resource types
        assert ResourceTypeRegistry.get_resource_type("BaseResource") == base_type
        assert ResourceTypeRegistry.get_resource_type("ExtendedResource") == extended_type
        assert ResourceTypeRegistry.get_resource_type("SpecializedResource") == specialized_type


class TestAST:
    """Test AST nodes for resource definitions."""

    def test_resource_definition(self):
        """Test ResourceDefinition AST node."""
        # Without parent (composition-based)
        definition = ResourceDefinition(name="MyResource", fields=[], methods=[])

        assert definition.name == "MyResource"

    def test_resource_field(self):
        """Test ResourceField AST node."""
        field = ResourceField(name="timeout", type_hint=TypeHint(name="int"), default_value=None, comment="Request timeout in seconds")

        assert field.name == "timeout"
        assert field.type_hint.name == "int"
        assert field.comment == "Request timeout in seconds"


if __name__ == "__main__":
    pytest.main([__file__])
