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

    def test_resource_type_inheritance(self):
        """Test resource type inheritance."""
        parent_type = ResourceType(
            name="BaseResource",
            fields={"name": "str", "kind": "str"},
            field_order=["name", "kind"],
            field_defaults={"kind": "base"},
        )

        child_type = ResourceType(
            name="ChildResource",
            fields={"extra_field": "int"},
            field_order=["extra_field"],
            field_defaults={"extra_field": 42},
            parent_type=parent_type,
        )

        # Check inheritance
        assert child_type.parent_type == parent_type
        assert "name" in child_type.fields  # Inherited
        assert "kind" in child_type.fields  # Inherited
        assert "extra_field" in child_type.fields  # Own field
        assert child_type.field_order == ["state", "name", "kind", "extra_field"]
        assert child_type.field_defaults["kind"] == "base"  # Inherited
        assert child_type.field_defaults["extra_field"] == 42  # Own default
        assert child_type.field_defaults["state"] == "CREATED"  # Built-in

    def test_inheritance_chain(self):
        """Test getting inheritance chain."""
        grandparent = ResourceType(name="Grandparent", fields={"id": "str"}, field_order=["id"])
        parent = ResourceType(name="Parent", fields={"name": "str"}, field_order=["name"], parent_type=grandparent)
        child = ResourceType(name="Child", fields={"value": "int"}, field_order=["value"], parent_type=parent)

        chain = child.get_inheritance_chain()
        assert [rt.name for rt in chain] == ["Grandparent", "Parent", "Child"]


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
        assert instance.state == "CREATED"

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

    def test_method_inheritance(self):
        """Test method inheritance in resource instances."""
        # Create parent type with method
        parent_type = ResourceType(
            name="BaseResource",
            fields={"name": "str"},
            field_order=["name"],
        )

        # Create child type
        child_type = ResourceType(
            name="ChildResource",
            fields={"extra": "str"},
            field_order=["extra"],
            parent_type=parent_type,
        )

        # Create instance
        instance = ResourceInstance(child_type, {"name": "test", "extra": "value"})

        # Test that instance can access parent fields
        assert instance.name == "test"
        assert instance.extra == "value"


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

    def test_inheritance_queries(self):
        """Test inheritance-related queries."""
        # Create inheritance chain
        base_type = ResourceType(name="BaseResource", fields={"id": "str"}, field_order=["id"])
        child_type = ResourceType(name="ChildResource", fields={"name": "str"}, field_order=["name"], parent_type=base_type)
        grandchild_type = ResourceType(name="GrandchildResource", fields={"value": "int"}, field_order=["value"], parent_type=child_type)

        ResourceTypeRegistry.register_resource(base_type)
        ResourceTypeRegistry.register_resource(child_type)
        ResourceTypeRegistry.register_resource(grandchild_type)

        # Test inheritance chain
        chain = ResourceTypeRegistry.get_inheritance_chain("GrandchildResource")
        assert chain == ["BaseResource", "ChildResource", "GrandchildResource"]

        # Test subtypes
        subtypes = ResourceTypeRegistry.get_all_subtypes("BaseResource")
        assert "ChildResource" in subtypes
        assert "GrandchildResource" in subtypes

        subtypes = ResourceTypeRegistry.get_all_subtypes("ChildResource")
        assert "GrandchildResource" in subtypes
        assert "BaseResource" not in subtypes


class TestAST:
    """Test AST nodes for resource definitions."""

    def test_resource_definition(self):
        """Test ResourceDefinition AST node."""
        definition = ResourceDefinition(name="MyResource", parent_name="BaseResource", fields=[], methods=[])

        assert definition.name == "MyResource"
        assert definition.parent_name == "BaseResource"

    def test_resource_field(self):
        """Test ResourceField AST node."""
        field = ResourceField(name="timeout", type_hint=TypeHint(name="int"), default_value=None, comment="Request timeout in seconds")

        assert field.name == "timeout"
        assert field.type_hint.name == "int"
        assert field.comment == "Request timeout in seconds"


if __name__ == "__main__":
    pytest.main([__file__])
