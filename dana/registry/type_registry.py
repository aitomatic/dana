"""
Type Registry for Dana

Specialized registry for agent, resource, and struct type definitions.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from typing import Any


class TypeRegistry:
    """Unified type registry with specialized storage for different type categories.

    This registry maintains separate storage for agent types, resource types, and struct types,
    while providing a unified interface for type registration and lookup.
    """

    def __init__(self):
        """Initialize the type registry with specialized storage."""
        # Type storage by category
        self._agent_types: dict[str, Any] = {}
        self._resource_types: dict[str, Any] = {}
        self._struct_types: dict[str, Any] = {}

        # Type metadata storage
        self._type_metadata: dict[str, dict[str, Any]] = {}

        # Registration order tracking
        self._registration_order: list[str] = []

    # === Agent Type Methods ===

    def register_agent_type(self, agent_type: Any) -> None:
        """Register an agent type.

        Args:
            agent_type: The agent type to register
        """
        if not hasattr(agent_type, "name"):
            raise ValueError("Agent type must have a 'name' attribute")

        name = agent_type.name
        if name in self._agent_types:
            # Check if this is the same agent definition (idempotent registration)
            existing = self._agent_types[name]
            if self._types_equal(agent_type, existing):
                return  # Same definition, don't re-register
            else:
                raise ValueError(f"Agent type '{name}' is already registered with different definition")

        self._agent_types[name] = agent_type
        # Also register in struct types for instantiation compatibility
        self._struct_types[name] = agent_type
        self._type_metadata[name] = {
            "category": "agent",
            "registered_at": self._get_timestamp(),
        }
        self._registration_order.append(name)

    def get_agent_type(self, name: str) -> Any | None:
        """Get an agent type by name.

        Args:
            name: The name of the agent type

        Returns:
            The agent type or None if not found
        """
        return self._agent_types.get(name)

    def list_agent_types(self) -> list[str]:
        """List all registered agent type names.

        Returns:
            List of agent type names in registration order
        """
        return [name for name in self._registration_order if name in self._agent_types]

    def has_agent_type(self, name: str) -> bool:
        """Check if an agent type is registered.

        Args:
            name: The name of the agent type

        Returns:
            True if the agent type is registered
        """
        return name in self._agent_types

    # === Resource Type Methods ===

    def register_resource_type(self, resource_type: Any) -> None:
        """Register a resource type.

        Args:
            resource_type: The resource type to register
        """
        if not hasattr(resource_type, "name"):
            raise ValueError("Resource type must have a 'name' attribute")

        name = resource_type.name
        if name in self._resource_types:
            # Check if this is the same resource definition (idempotent registration)
            existing = self._resource_types[name]
            if self._types_equal(resource_type, existing):
                return  # Same definition, don't re-register
            else:
                raise ValueError(f"Resource type '{name}' is already registered with different definition")

        self._resource_types[name] = resource_type
        self._type_metadata[name] = {
            "category": "resource",
            "registered_at": self._get_timestamp(),
        }
        self._registration_order.append(name)

    def get_resource_type(self, name: str) -> Any | None:
        """Get a resource type by name.

        Args:
            name: The name of the resource type

        Returns:
            The resource type or None if not found
        """
        return self._resource_types.get(name)

    def list_resource_types(self) -> list[str]:
        """List all registered resource type names.

        Returns:
            List of resource type names in registration order
        """
        return [name for name in self._registration_order if name in self._resource_types]

    def has_resource_type(self, name: str) -> bool:
        """Check if a resource type is registered.

        Args:
            name: The name of the resource type

        Returns:
            True if the resource type is registered
        """
        return name in self._resource_types

    # === Struct Type Methods ===

    def register_struct_type(self, struct_type: Any) -> None:
        """Register a struct type.

        Args:
            struct_type: The struct type to register
        """
        if not hasattr(struct_type, "name"):
            raise ValueError("Struct type must have a 'name' attribute")

        name = struct_type.name
        if name in self._struct_types:
            # Check if this is the same struct definition (idempotent registration)
            existing = self._struct_types[name]
            if self._types_equal(struct_type, existing):
                return  # Same definition, don't re-register
            else:
                raise ValueError(f"Struct type '{name}' is already registered with different definition")

        self._struct_types[name] = struct_type
        self._type_metadata[name] = {
            "category": "struct",
            "registered_at": self._get_timestamp(),
        }
        self._registration_order.append(name)

    def get_struct_type(self, name: str) -> Any | None:
        """Get a struct type by name.

        Args:
            name: The name of the struct type

        Returns:
            The struct type or None if not found
        """
        return self._struct_types.get(name)

    def list_struct_types(self) -> list[str]:
        """List all registered struct type names.

        Returns:
            List of struct type names in registration order
        """
        return [name for name in self._registration_order if name in self._struct_types]

    def has_struct_type(self, name: str) -> bool:
        """Check if a struct type is registered.

        Args:
            name: The name of the struct type

        Returns:
            True if the struct type is registered
        """
        return name in self._struct_types

    # === Backward Compatibility Methods ===

    @classmethod
    def list_types(cls) -> list[str]:
        """List all registered struct type names (backward compatibility).

        Returns:
            List of struct type names
        """
        from dana.registry import TYPE_REGISTRY

        return TYPE_REGISTRY.list_struct_types()

    @classmethod
    def exists(cls, name: str) -> bool:
        """Check if a struct type exists (backward compatibility).

        Args:
            name: The name of the struct type

        Returns:
            True if the struct type exists
        """
        from dana.registry import TYPE_REGISTRY

        return TYPE_REGISTRY.has_struct_type(name)

    @classmethod
    def register(cls, struct_type: Any) -> None:
        """Register a struct type (backward compatibility).

        Args:
            struct_type: The struct type to register
        """
        from dana.registry import TYPE_REGISTRY

        TYPE_REGISTRY.register_struct_type(struct_type)

    @classmethod
    def create_instance(cls, struct_name: str, values: dict[str, Any]) -> Any:
        """Create a struct instance (backward compatibility).

        Args:
            struct_name: The name of the struct type
            values: The field values for the instance

        Returns:
            The created struct instance
        """
        from dana.agent import AgentInstance
        from dana.core.lang.interpreter.struct_system import StructInstance
        from dana.registry import TYPE_REGISTRY

        struct_type = TYPE_REGISTRY.get_struct_type(struct_name)
        if struct_type is None:
            raise ValueError(f"Unknown struct type '{struct_name}'")

        # Check if this is an agent type and create appropriate instance
        if TYPE_REGISTRY.has_agent_type(struct_name):
            return AgentInstance(struct_type, values)
        else:
            return StructInstance(struct_type, values)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered types (backward compatibility for testing)."""
        from dana.registry import TYPE_REGISTRY

        TYPE_REGISTRY.clear_instance()

    # === Generic Type Methods ===

    def get_type(self, name: str) -> Any | None:
        """Get any type by name (searches all categories).

        Args:
            name: The name of the type

        Returns:
            The type or None if not found
        """
        # Search in order: agent, resource, struct
        if name in self._agent_types:
            return self._agent_types[name]
        elif name in self._resource_types:
            return self._resource_types[name]
        elif name in self._struct_types:
            return self._struct_types[name]
        return None

    def has_type(self, name: str) -> bool:
        """Check if any type is registered with the given name.

        Args:
            name: The name of the type

        Returns:
            True if the type is registered in any category
        """
        return name in self._agent_types or name in self._resource_types or name in self._struct_types

    def list_all_types(self) -> list[str]:
        """List all registered type names across all categories.

        Returns:
            List of all type names in registration order
        """
        return self._registration_order.copy()

    def get_type_metadata(self, name: str) -> dict[str, Any] | None:
        """Get metadata for a type.

        Args:
            name: The name of the type

        Returns:
            Type metadata or None if not found
        """
        return self._type_metadata.get(name)

    def get_types_by_category(self, category: str) -> dict[str, Any]:
        """Get all types of a specific category.

        Args:
            category: The category ('agent', 'resource', or 'struct')

        Returns:
            Dictionary of type names to types
        """
        if category == "agent":
            return self._agent_types.copy()
        elif category == "resource":
            return self._resource_types.copy()
        elif category == "struct":
            return self._struct_types.copy()
        else:
            raise ValueError(f"Unknown category: {category}")

    # === Utility Methods ===

    def clear_instance(self) -> None:
        """Clear all registered types (for testing)."""
        self._agent_types.clear()
        self._resource_types.clear()
        self._struct_types.clear()
        self._type_metadata.clear()
        self._registration_order.clear()

    # Additional backward compatibility methods
    @classmethod
    def create_instance_from_json(cls, data: dict[str, Any], struct_name: str) -> Any:
        """Create a struct instance from JSON data (backward compatibility)."""
        from dana.registry import TYPE_REGISTRY

        struct_type = TYPE_REGISTRY.get_struct_type(struct_name)
        if struct_type is None:
            available_types = TYPE_REGISTRY.list_struct_types()
            raise ValueError(f"Unknown struct type '{struct_name}'. Available types: {available_types}")

        # Validate the JSON data first
        cls.validate_json_data(data, struct_name)

        # Create the instance
        from dana.agent import AgentInstance
        from dana.core.lang.interpreter.struct_system import StructInstance

        # Check if this is an agent type and create appropriate instance
        if TYPE_REGISTRY.has_agent_type(struct_name):
            return AgentInstance(struct_type, data)
        else:
            return StructInstance(struct_type, data)

    @classmethod
    def validate_json_data(cls, data: dict[str, Any], struct_name: str) -> bool:
        """Validate JSON data against struct schema (backward compatibility)."""
        from dana.registry import TYPE_REGISTRY

        struct_type = TYPE_REGISTRY.get_struct_type(struct_name)
        if struct_type is None:
            available_types = TYPE_REGISTRY.list_struct_types()
            raise ValueError(f"Unknown struct type '{struct_name}'. Available types: {available_types}")

        # Basic validation
        if not isinstance(data, dict):
            raise ValueError(f"Expected object for struct {struct_name}, got {type(data)}")

        # Check required fields
        required_fields = set()
        for field_name in struct_type.fields.keys():
            if struct_type.field_defaults is None or field_name not in struct_type.field_defaults:
                required_fields.add(field_name)

        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields for struct '{struct_name}': {sorted(missing_fields)}")

        # Check for extra fields (if struct doesn't allow them)
        extra_fields = set(data.keys()) - set(struct_type.fields.keys())
        if extra_fields:
            raise ValueError(f"Unknown fields for struct '{struct_name}': {sorted(extra_fields)}")

        return True

    @classmethod
    def get(cls, struct_name: str) -> Any | None:
        """Get a struct type by name (backward compatibility)."""
        from dana.registry import TYPE_REGISTRY

        return TYPE_REGISTRY.get_struct_type(struct_name)

    @classmethod
    def get_schema(cls, struct_name: str) -> dict[str, Any]:
        """Get JSON schema for a struct type (backward compatibility)."""
        from dana.registry import TYPE_REGISTRY

        struct_type = TYPE_REGISTRY.get_struct_type(struct_name)
        if struct_type is None:
            available_types = TYPE_REGISTRY.list_struct_types()
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
        from dana.registry import TYPE_REGISTRY

        if TYPE_REGISTRY.has_struct_type(type_name):
            return {"type": "object", "description": f"Reference to {type_name} struct", "$ref": f"#/definitions/{type_name}"}

        # Unknown type - treat as any
        return {"description": f"Unknown type: {type_name}"}

    def count(self) -> int:
        """Get the total number of registered types."""
        return len(self._registration_order)

    def is_empty(self) -> bool:
        """Check if the registry is empty."""
        return len(self._registration_order) == 0

    def _types_equal(self, type1: Any, type2: Any) -> bool:
        """Check if two types have the same structure.

        This is used for idempotent registration - if the types have the same
        structure, we don't re-register them.
        """
        # Check if they have the same fields
        if hasattr(type1, "fields") and hasattr(type2, "fields"):
            if type1.fields != type2.fields:
                return False

        # Check if they have the same field order
        if hasattr(type1, "field_order") and hasattr(type2, "field_order"):
            if type1.field_order != type2.field_order:
                return False

        # Check if they have the same field defaults
        if hasattr(type1, "field_defaults") and hasattr(type2, "field_defaults"):
            if type1.field_defaults != type2.field_defaults:
                return False

        return True

    def _get_timestamp(self) -> float:
        """Get current timestamp for registration tracking."""
        import time

        return time.time()

    def __repr__(self) -> str:
        """String representation of the type registry."""
        return (
            f"TypeRegistry("
            f"agent_types={len(self._agent_types)}, "
            f"resource_types={len(self._resource_types)}, "
            f"struct_types={len(self._struct_types)}, "
            f"total={len(self._registration_order)}"
            f")"
        )
