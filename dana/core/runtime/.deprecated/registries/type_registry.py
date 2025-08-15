"""
Type registries for Dana struct and resource types.

Centralized type management for Dana's type system.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from dana.core.lang.interpreter.struct_system import StructType, StructInstance
    from dana.core.resource.resource_type import ResourceType, ResourceInstance


class StructTypeRegistry:
    """Global registry for struct types."""

    _instance: Optional["StructTypeRegistry"] = None
    _types: dict[str, "StructType"] = {}

    def __new__(cls) -> "StructTypeRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, struct_type: "StructType") -> None:
        """Register a new struct type."""
        if struct_type.name in cls._types:
            # Check if this is the same struct definition
            existing_struct = cls._types[struct_type.name]
            if existing_struct.fields == struct_type.fields and existing_struct.field_order == struct_type.field_order:
                # Same struct definition - allow idempotent registration
                return
            else:
                raise ValueError(
                    f"Struct type '{struct_type.name}' is already registered with different definition. Struct names must be unique."
                )

        cls._types[struct_type.name] = struct_type

    @classmethod
    def get(cls, struct_name: str) -> "StructType | None":
        """Get a struct type by name."""
        return cls._types.get(struct_name)

    @classmethod
    def exists(cls, struct_name: str) -> bool:
        """Check if a struct type is registered."""
        return struct_name in cls._types

    @classmethod
    def list_types(cls) -> list[str]:
        """Get list of all registered struct type names."""
        return sorted(cls._types.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered struct types (for testing)."""
        cls._types.clear()

    @classmethod
    def create_instance(cls, struct_name: str, values: dict[str, Any]) -> "StructInstance":
        """Create a struct instance by name."""
        struct_type = cls.get(struct_name)
        if struct_type is None:
            available_types = cls.list_types()
            raise ValueError(f"Unknown struct type '{struct_name}'. Available types: {available_types}")

        # Check if this is an agent struct type
        try:
            from dana.agent import AgentInstance, AgentType

            if isinstance(struct_type, AgentType):
                return AgentInstance(struct_type, values)
        except ImportError:
            pass

        # Check if this is a resource type (delegate to resource registry)
        try:
            from dana.core.runtime.registries.resource_registry import ResourceTypeRegistry

            if ResourceTypeRegistry.exists(struct_name):
                return ResourceTypeRegistry.create_resource_instance(struct_name, values)
        except ImportError:
            # Fallback to old location for backward compatibility
            try:
                from dana.core.resource.resource_registry import ResourceTypeRegistry

                if ResourceTypeRegistry.exists(struct_name):
                    return ResourceTypeRegistry.create_resource_instance(struct_name, values)
            except ImportError:
                pass

        # Import here to avoid circular imports
        from dana.core.lang.interpreter.struct_system import StructInstance

        return StructInstance(struct_type, values)

    @classmethod
    def get_schema(cls, struct_name: str) -> dict[str, Any]:
        """Get JSON schema for a struct type.

        Args:
            struct_name: Name of the struct type

        Returns:
            JSON schema dictionary for the struct

        Raises:
            ValueError: If struct type not found
        """
        struct_type = cls.get(struct_name)
        if struct_type is None:
            available_types = cls.list_types()
            raise ValueError(f"Unknown struct type '{struct_name}'. Available types: {available_types}")

        # Generate JSON schema
        properties = {}
        required = []

        for field_name in struct_type.field_order:
            field_type = struct_type.fields[field_name]
            properties[field_name] = cls._type_to_json_schema(field_type)
            required.append(field_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
            "title": struct_name,
            "description": f"Schema for {struct_name} struct",
        }

    @classmethod
    def _type_to_json_schema(cls, type_name: str) -> dict[str, Any]:
        """Convert Dana type name to JSON schema type definition."""
        type_mapping = {
            "str": {"type": "string"},
            "int": {"type": "integer"},
            "float": {"type": "number"},
            "bool": {"type": "boolean"},
            "list": {"type": "array"},
            "dict": {"type": "object"},
            "any": {},  # Accept any type
        }

        # Check for built-in types first
        if type_name in type_mapping:
            return type_mapping[type_name]

        # Check for registered struct types
        if cls.exists(type_name):
            return {"type": "object", "description": f"Reference to {type_name} struct", "$ref": f"#/definitions/{type_name}"}

        # Unknown type - treat as any
        return {"description": f"Unknown type: {type_name}"}

    @classmethod
    def validate_json(cls, json_data: dict[str, Any], struct_name: str) -> bool:
        """Validate JSON data against struct schema.

        Args:
            json_data: JSON data to validate
            struct_name: Name of the struct type to validate against

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails or struct type not found
        """
        schema = cls.get_schema(struct_name)

        # Basic validation - could be enhanced with jsonschema library
        if not isinstance(json_data, dict):
            raise ValueError(f"Expected object for struct {struct_name}, got {type(json_data)}")

        # Check required fields
        for field_name in schema.get("required", []):
            if field_name not in json_data:
                raise ValueError(f"Missing required field '{field_name}' for struct {struct_name}")

        # Check for extra fields
        if not schema.get("additionalProperties", True):
            for field_name in json_data:
                if field_name not in schema.get("properties", {}):
                    raise ValueError(f"Unexpected field '{field_name}' for struct {struct_name}")

        return True


class ResourceTypeRegistry:
    """Efficient registry for resource types only (no instance tracking)."""

    _instance: Optional["ResourceTypeRegistry"] = None
    _resource_types: dict[str, "ResourceType"] = {}

    def __new__(cls) -> "ResourceTypeRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_resource(cls, resource_type: "ResourceType") -> None:
        """Register a resource type."""
        if resource_type.name in cls._resource_types:
            # Check if this is the same resource definition
            existing_type = cls._resource_types[resource_type.name]
            if existing_type.fields == resource_type.fields and existing_type.field_order == resource_type.field_order:
                # Same resource definition - allow idempotent registration
                return
            else:
                raise ValueError(f"Resource type '{resource_type.name}' is already registered with different definition")

        cls._resource_types[resource_type.name] = resource_type

    @classmethod
    def get_resource_type(cls, name: str) -> "ResourceType | None":
        """Get a resource type by name."""
        return cls._resource_types.get(name)

    @classmethod
    def exists(cls, name: str) -> bool:
        """Check if a resource type is registered."""
        return name in cls._resource_types

    @classmethod
    def list_resource_types(cls) -> list[str]:
        """List all registered resource type names."""
        return sorted(cls._resource_types.keys())

    @classmethod
    def create_resource_instance(cls, resource_name: str, values: dict[str, Any] | None = None) -> "ResourceInstance":
        """Create a resource instance by name.

        Args:
            resource_name: Name of the resource type
            values: Optional initial values for the resource

        Returns:
            New resource instance

        Raises:
            ValueError: If resource type not found
        """
        resource_type = cls.get_resource_type(resource_name)
        if resource_type is None:
            available_types = cls.list_resource_types()
            raise ValueError(f"Unknown resource type '{resource_name}'. Available types: {available_types}")

        # Import here to avoid circular imports
        from dana.core.resource.resource_instance import ResourceInstance

        return ResourceInstance(resource_type, values or {})

    @classmethod
    def clear(cls) -> None:
        """Clear all registered resource types (for testing)."""
        cls._resource_types.clear()
