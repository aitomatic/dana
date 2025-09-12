"""
Resource Type

Extends StructType to add resource-specific functionality while maintaining
compatibility with the struct system.
"""

from typing import Any

from dana.common.utils.misc import Misc
from dana.core.builtins.struct_system import StructType

# Import lazily where used to avoid circular import during module import


class ResourceType(StructType):
    """
    Resource type that extends StructType with resource-specific functionality.

    Resources are structs with additional lifecycle management capabilities.
    """

    def __init__(
        self,
        name: str,
        fields: dict[str, str],
        field_order: list[str],
        field_defaults: dict[str, Any] | None = None,
        field_comments: dict[str, str] | None = None,
        docstring: str | None = None,
    ):
        """
        Initialize a resource type.

        Args:
            name: Resource type name
            fields: Field name to type mapping
            field_order: Order of fields
            field_defaults: Default values for fields
            field_comments: Comments for fields
            docstring: Documentation string
        """
        # Initialize as a regular StructType first

        # Resource must have a name, description, and id
        # Validate resource type has a name field
        additional_fields = {}
        additional_field_defaults = {}
        if fields and "name" not in fields:
            additional_fields["name"] = "str"
            additional_field_defaults["name"] = name
        if fields and "description" not in fields:
            additional_fields["description"] = "str"
            additional_field_defaults["description"] = f"Description for {name}"
        if fields and "id" not in fields:
            additional_fields["id"] = "str"
            additional_field_defaults["id"] = Misc.generate_uuid(8)

        # Update the instance-specific resource type (not the shared one)
        fields.update(additional_fields)
        if field_defaults:
            field_defaults.update(additional_field_defaults)
        else:
            field_defaults = additional_field_defaults
        field_order.extend(list(additional_fields.keys()))

        super().__init__(
            name=name,
            fields=fields,
            field_order=field_order,
            field_comments=field_comments or {},
            field_defaults=field_defaults,
            docstring=docstring,
        )

        # Enable lifecycle management
        self.has_lifecycle = True

    def __post_init__(self):
        """Initialize default resource methods and add default resource fields."""
        # Add default resource fields automatically
        from .resource_instance import ResourceInstance

        additional_fields = ResourceInstance.get_default_resource_fields()
        self.merge_additional_fields(additional_fields)

        # Register default resource methods (defined by ResourceInstance)
        default_methods = ResourceInstance.get_default_dana_methods()
        for method_name, method in default_methods.items():
            self.add_resource_method(method_name, method)

        # Call parent's post-init last
        super().__post_init__()

    def has_method(self, method_name: str) -> bool:
        """Check if this resource type has a method."""
        # Check unified FUNCTION_REGISTRY
        from dana.registry import FUNCTION_REGISTRY

        if FUNCTION_REGISTRY.lookup_struct_function(self.name, method_name):
            return True

        # Check current type attributes
        if hasattr(self, method_name):
            return True

        return False

    def add_resource_method(self, method_name: str, method: Any) -> None:
        """Add a resource-specific method to the unified FUNCTION_REGISTRY."""
        from dana.registry import FUNCTION_REGISTRY

        FUNCTION_REGISTRY.register_struct_function(self.name, method_name, method)

    def get_resource_method(self, method_name: str) -> Any | None:
        """Get a resource method by name."""
        from dana.registry import FUNCTION_REGISTRY

        return FUNCTION_REGISTRY.lookup_struct_function(self.name, method_name)
