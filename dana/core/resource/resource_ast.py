"""
Resource AST Processing

Functions to create ResourceType from AST nodes.
"""

from typing import Any

from dana.core.lang.ast import FunctionDefinition, ResourceDefinition
from dana.core.lang.interpreter.functions.dana_function import DanaFunction
from dana.registry import FUNCTION_REGISTRY

from .resource_type import ResourceType


def create_resource_type_from_ast(resource_def: ResourceDefinition, context=None) -> ResourceType:
    """
    Create a ResourceType from a ResourceDefinition AST node.

    Processes resource methods as FunctionDefinition nodes and registers them.

    Args:
        resource_def: The ResourceDefinition AST node
        context: Optional sandbox context for evaluating default values

    Returns:
        ResourceType with fields and default values
    """
    # Initialize fields and metadata
    fields: dict[str, str] = {}
    field_order: list[str] = []
    field_defaults: dict[str, Any] = {}
    field_comments: dict[str, str] = {}

    # Process resource fields
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

    # Create the resource type
    resource_type = ResourceType(
        name=resource_def.name,
        fields=fields,
        field_order=field_order,
        field_defaults=field_defaults if field_defaults else None,
        field_comments=field_comments,
        docstring=resource_def.docstring,
    )

    # Process resource methods (FunctionDefinition nodes)
    for method_def in resource_def.methods:
        if isinstance(method_def, FunctionDefinition):
            # Create DanaFunction from FunctionDefinition
            dana_func = _create_dana_function_from_definition(method_def, context)

            # Register the method in unified registry
            # Resource methods are registered with the resource type name as the receiver type
            FUNCTION_REGISTRY.register_struct_function(resource_def.name, method_def.name.name, dana_func)

    return resource_type


def _create_dana_function_from_definition(func_def: FunctionDefinition, context=None) -> DanaFunction:
    """
    Create a DanaFunction from a FunctionDefinition AST node.

    Args:
        func_def: The FunctionDefinition node
        context: Optional execution context

    Returns:
        DanaFunction object
    """
    # Extract parameter names and defaults
    param_names = []
    param_defaults = {}

    # Handle parameters (including receiver if present)
    all_params = []
    if func_def.receiver:
        all_params.append(func_def.receiver)
    all_params.extend(func_def.parameters)

    for param in all_params:
        if hasattr(param, "name"):
            param_name = param.name
            param_names.append(param_name)

            # Extract default value if present
            if hasattr(param, "default_value") and param.default_value is not None:
                param_defaults[param_name] = param.default_value

    # Create DanaFunction
    return DanaFunction(
        name=func_def.name.name,
        parameters=param_names,
        defaults=param_defaults,
        body=func_def.body,
        return_type=func_def.return_type,
        decorators=func_def.decorators,
        is_sync=func_def.is_sync,
        location=func_def.location,
    )
