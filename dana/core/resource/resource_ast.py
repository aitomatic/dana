"""
Resource AST Processing

Functions to create ResourceType from AST nodes with inheritance support.
"""

from typing import Any

from dana.core.lang.ast import ResourceDefinition
from dana.core.lang.interpreter.struct_system import StructTypeRegistry

from .resource_type import ResourceType


def create_resource_type_from_ast(resource_def: ResourceDefinition, context=None) -> ResourceType:
    """
    Create a ResourceType from a ResourceDefinition AST node.

    Handles inheritance by merging parent fields and defaults.

    Args:
        resource_def: The ResourceDefinition AST node
        context: Optional sandbox context for evaluating default values

    Returns:
        ResourceType with fields and default values, including inherited fields
    """
    # Start with inherited fields if parent exists
    fields: dict[str, str] = {}
    field_order: list[str] = []
    field_defaults: dict[str, Any] = {}
    field_comments: dict[str, str] = {}
    parent_type: ResourceType | None = None

    # Handle inheritance by merging parent fields
    if resource_def.parent_name:
        parent_type = StructTypeRegistry.get(resource_def.parent_name)
        if parent_type is None:
            raise ValueError(f"Parent resource '{resource_def.parent_name}' not found for '{resource_def.name}'")

        # Copy parent fields first (inheritance order: parent fields come first)
        fields.update(parent_type.fields)
        field_order.extend(parent_type.field_order)

        if parent_type.field_defaults:
            field_defaults.update(parent_type.field_defaults)

        if hasattr(parent_type, "field_comments") and parent_type.field_comments:
            field_comments.update(parent_type.field_comments)

    # Add child fields (child fields override parent fields with same name)
    for field in resource_def.fields:
        if field.type_hint is None:
            raise ValueError(f"Field {field.name} has no type hint")
        if not hasattr(field.type_hint, "name"):
            raise ValueError(f"Field {field.name} type hint {field.type_hint} has no name attribute")

        # Add or override field
        fields[field.name] = field.type_hint.name

        # Update field order (remove if exists, then add to end)
        if field.name in field_order:
            field_order.remove(field.name)
        field_order.append(field.name)

        if field.default_value is not None:
            field_defaults[field.name] = field.default_value

        if getattr(field, "comment", None):
            field_comments[field.name] = field.comment

    return ResourceType(
        name=resource_def.name,
        fields=fields,
        field_order=field_order,
        field_defaults=field_defaults if field_defaults else None,
        field_comments=field_comments,
        docstring=resource_def.docstring,
    )
