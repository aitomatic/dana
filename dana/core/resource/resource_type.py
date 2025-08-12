"""
Resource Type

Extends StructType to add resource-specific functionality while maintaining
compatibility with the struct system.
"""

from typing import Any, Optional

from dana.core.lang.interpreter.struct_system import StructType, TypeAwareMethodRegistry


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
        parent_type: Optional["ResourceType"] = None,
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
            parent_type: Parent resource type for inheritance
            docstring: Documentation string
        """
        # Handle inheritance by merging parent fields
        inherited_fields = {}
        inherited_field_order = []
        inherited_defaults = {}
        inherited_comments = {}

        if parent_type:
            # Inherit fields from parent
            inherited_fields.update(parent_type.fields)
            inherited_field_order.extend(parent_type.field_order)
            if parent_type.field_defaults:
                inherited_defaults.update(parent_type.field_defaults)
            if parent_type.field_comments:
                inherited_comments.update(parent_type.field_comments)
        else:
            # Ensure all resources have a state field if no parent
            inherited_fields = {"state": "str"}
            inherited_field_order = ["state"]
            inherited_defaults = {"state": "CREATED"}
            inherited_comments = {"state": "Current state of the resource"}

        # Merge with current type's fields
        enhanced_fields = {**inherited_fields, **fields}
        enhanced_field_order = inherited_field_order + field_order
        enhanced_defaults = {**inherited_defaults, **(field_defaults or {})}
        enhanced_comments = {**inherited_comments, **(field_comments or {})}

        # Initialize as StructType
        super().__init__(
            name=name,
            fields=enhanced_fields,
            field_order=enhanced_field_order,
            field_comments=enhanced_comments,
            field_defaults=enhanced_defaults,
            docstring=docstring,
        )

        # Store parent type for inheritance
        self._parent_type = parent_type

        # Enable lifecycle management
        self.has_lifecycle = True

    def has_method(self, method_name: str) -> bool:
        """Check if this resource type or any parent has a method."""
        # Check TypeAwareMethodRegistry first
        if TypeAwareMethodRegistry.lookup_method(self.name, method_name):
            return True

        # Check current type attributes
        if hasattr(self, method_name):
            return True

        # Check parent types
        parent = self.parent_type
        while parent:
            if hasattr(parent, method_name):
                return True
            if TypeAwareMethodRegistry.lookup_method(parent.name, method_name):
                return True
            parent = getattr(parent, "parent_type", None)

        return False

    @property
    def parent_type(self) -> Optional["ResourceType"]:
        """Get the parent resource type."""
        return getattr(self, "_parent_type", None)

    def get_inheritance_chain(self) -> list["ResourceType"]:
        """Get the inheritance chain for this resource type."""
        chain = []
        current = self
        while current:
            chain.append(current)
            current = current.parent_type
        return list(reversed(chain))

    def add_resource_method(self, method_name: str, method: Any) -> None:
        """Add a resource-specific method to the TypeAwareMethodRegistry."""
        TypeAwareMethodRegistry.register_method(self.name, method_name, method)

    def get_resource_method(self, method_name: str) -> Any | None:
        """Get a resource method by name."""
        return TypeAwareMethodRegistry.lookup_method(self.name, method_name)
