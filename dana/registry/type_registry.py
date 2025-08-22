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
        self._interface_types: dict[str, Any] = {}
        self._workflow_types: dict[str, Any] = {}

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

    # === Workflow Type Methods ===

    def register_workflow_type(self, workflow_type: Any) -> None:
        """Register a workflow type.

        Args:
            workflow_type: The workflow type to register
        """
        if not hasattr(workflow_type, "name"):
            raise ValueError("Workflow type must have a 'name' attribute")

        name = workflow_type.name
        if name in self._workflow_types:
            # Check if this is the same workflow definition (idempotent registration)
            existing = self._workflow_types[name]
            if self._types_equal(workflow_type, existing):
                return  # Same definition, don't re-register
            else:
                raise ValueError(f"Workflow type '{name}' is already registered with different definition")

        self._workflow_types[name] = workflow_type
        # Also register in struct types for instantiation compatibility
        self._struct_types[name] = workflow_type
        self._type_metadata[name] = {
            "category": "workflow",
            "registered_at": self._get_timestamp(),
        }
        self._registration_order.append(name)

    def get_workflow_type(self, name: str) -> Any | None:
        """Get a workflow type by name.

        Args:
            name: The name of the workflow type

        Returns:
            The workflow type or None if not found
        """
        return self._workflow_types.get(name)

    def list_workflow_types(self) -> list[str]:
        """List all registered workflow type names.

        Returns:
            List of workflow type names in registration order
        """
        return [name for name in self._registration_order if name in self._workflow_types]

    def has_workflow_type(self, name: str) -> bool:
        """Check if a workflow type is registered.

        Args:
            name: The name of the workflow type

        Returns:
            True if the workflow type is registered
        """
        return name in self._workflow_types

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

    # === Interface Type Methods ===

    def register_interface_type(self, interface_type: Any) -> None:
        """Register an interface type.

        Args:
            interface_type: The interface type to register
        """
        if not hasattr(interface_type, "name"):
            raise ValueError("Interface type must have a 'name' attribute")

        name = interface_type.name
        if name in self._interface_types:
            # Check if this is the same interface definition (idempotent registration)
            existing = self._interface_types[name]
            if self._types_equal(interface_type, existing):
                return  # Same definition, don't re-register
            else:
                raise ValueError(f"Interface type '{name}' is already registered with different definition")

        self._interface_types[name] = interface_type
        self._type_metadata[name] = {
            "category": "interface",
            "registered_at": self._get_timestamp(),
        }
        self._registration_order.append(name)

    def get_interface_type(self, name: str) -> Any | None:
        """Get an interface type by name.

        Args:
            name: The name of the interface type

        Returns:
            The interface type or None if not found
        """
        return self._interface_types.get(name)

    def list_interface_types(self) -> list[str]:
        """List all registered interface type names.

        Returns:
            List of interface type names in registration order
        """
        return [name for name in self._registration_order if name in self._interface_types]

    def has_interface_type(self, name: str) -> bool:
        """Check if an interface type is registered.

        Args:
            name: The name of the interface type

        Returns:
            True if the interface type is registered
        """
        return name in self._interface_types

    # === Unified Type Methods ===

    def get_type(self, name: str) -> Any | None:
        """Get any type by name (searches all categories).

        Args:
            name: The name of the type

        Returns:
            The type or None if not found
        """
        # Search in order: agent, resource, struct, interface
        if name in self._agent_types:
            return self._agent_types[name]
        elif name in self._resource_types:
            return self._resource_types[name]
        elif name in self._struct_types:
            return self._struct_types[name]
        elif name in self._interface_types:
            return self._interface_types[name]
        return None

    def has_type(self, name: str) -> bool:
        """Check if any type is registered with the given name.

        Args:
            name: The name of the type

        Returns:
            True if the type is registered in any category
        """
        return name in self._agent_types or name in self._resource_types or name in self._struct_types or name in self._interface_types

    def list_all_types(self) -> list[str]:
        """List all registered type names across all categories.

        Returns:
            List of all type names in registration order
        """
        return self._registration_order.copy()

    def list_types(self) -> list[str]:
        """List all registered type names (alias for list_all_types for backward compatibility).

        Returns:
            List of all type names in registration order
        """
        return self.list_all_types()

    def exists(self, name: str) -> bool:
        """Check if a type exists in any category.

        Args:
            name: The name of the type to check

        Returns:
            True if the type exists in any category
        """
        return self.has_type(name)

    def clear(self) -> None:
        """Clear all registries (alias for clear_instance for backward compatibility)."""
        self.clear_instance()

    def create_instance(self, struct_name: str, data: dict[str, Any]) -> Any:
        """Create a struct instance from JSON data (alias for create_instance_from_json).

        Args:
            struct_name: The name of the struct type
            data: The data to create the instance from

        Returns:
            The created struct instance
        """
        return self.create_instance_from_json(data, struct_name)

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
            category: The category ('agent', 'resource', 'struct', or 'interface')

        Returns:
            Dictionary of type names to types
        """
        if category == "agent":
            return self._agent_types.copy()
        elif category == "resource":
            return self._resource_types.copy()
        elif category == "struct":
            return self._struct_types.copy()
        elif category == "interface":
            return self._interface_types.copy()
        else:
            raise ValueError(f"Unknown category: {category}")

    def register(self, type_obj: Any) -> None:
        """Register a type object (automatically determines category).

        Args:
            type_obj: The type object to register
        """
        if not hasattr(type_obj, "name"):
            raise ValueError("Type object must have a 'name' attribute")

        # Use explicit type detection for better reliability
        category = self._detect_type_category(type_obj)

        if category == "agent":
            self.register_agent_type(type_obj)
        elif category == "resource":
            self.register_resource_type(type_obj)
        elif category == "interface":
            self.register_interface_type(type_obj)
        elif category == "struct":
            self.register_struct_type(type_obj)
        else:
            # Fallback to struct type for backward compatibility
            self.register_struct_type(type_obj)

    def _detect_type_category(self, type_obj: Any) -> str:
        """Detect the category of a type object using explicit checks.

        Args:
            type_obj: The type object to categorize

        Returns:
            Category string: "agent", "resource", "interface", or "struct"
        """
        # Check for explicit type attributes first (most reliable)
        if hasattr(type_obj, "__class__"):
            class_name = type_obj.__class__.__name__

            # Check for agent types (including agent_blueprint)
            if class_name == "AgentType" or (hasattr(type_obj, "memory_system") and hasattr(type_obj, "reasoning_capabilities")):
                return "agent"

            # Check for resource types
            if class_name == "ResourceType" or (hasattr(type_obj, "has_lifecycle") and type_obj.has_lifecycle):
                return "resource"

            # Check for interface types
            if class_name == "InterfaceType" or (hasattr(type_obj, "methods") and hasattr(type_obj, "embedded_interfaces")):
                return "interface"

            # Check for struct types (default)
            if class_name == "StructType":
                return "struct"

        # Fallback to struct type for backward compatibility
        return "struct"

    # === Utility Methods ===

    def clear_instance(self) -> None:
        """Clear all registered types (for testing)."""
        self._agent_types.clear()
        self._resource_types.clear()
        self._struct_types.clear()
        self._interface_types.clear()
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
        from dana.core.builtin_types.agent_system import AgentInstance
        from dana.core.builtin_types.struct_system import StructInstance

        # Check if this is an agent type and create appropriate instance
        if TYPE_REGISTRY.has_agent_type(struct_name):
            return AgentInstance(struct_type, data)
        elif TYPE_REGISTRY.has_workflow_type(struct_name):
            from dana.core.builtin_types.workflow_system import WorkflowInstance

            return WorkflowInstance(struct_type, data)
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
