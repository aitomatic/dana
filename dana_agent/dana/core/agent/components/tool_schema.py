"""
Tool Schema Generator for Native Function Calling

Generates OpenAI-compatible tool schemas from DANA resources and workflows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dana.common.protocols.war import IS_TOOL_USE
from dana.common.utils.misc import Misc

if TYPE_CHECKING:
    from dana.common.protocols import AgentProtocol, ResourceProtocol, WorkflowProtocol


# Map Python types to JSON Schema types
PYTHON_TO_JSON_TYPE = {
    "str": "string",
    "string": "string",
    "int": "integer",
    "integer": "integer",
    "float": "number",
    "number": "number",
    "bool": "boolean",
    "boolean": "boolean",
    "list": "array",
    "dict": "object",
    "None": "null",
    "Any": "string",  # Default to string for Any
}


def _python_type_to_json_schema(python_type: str) -> str:
    """Convert Python type string to JSON Schema type."""
    # Handle common type variations
    base_type = python_type.split("[")[0].strip()  # Remove generics like list[str]
    base_type = base_type.replace("Optional[", "").replace("]", "")

    return PYTHON_TO_JSON_TYPE.get(base_type, "string")


def _method_signature_to_schema(
    method_sig: Any,
    object_id: str,
    object_type: str = "resource",
) -> dict:
    """Convert a MethodSignature to OpenAI function schema format.

    Args:
        method_sig: MethodSignature object from Misc.parse_method_signature
        object_id: The resource/workflow ID
        object_type: Either "resource" or "workflow"

    Returns:
        OpenAI-compatible tool schema dictionary
    """
    # Build function name: object_id__method_name (OpenAI requires ^[a-zA-Z0-9_-]+$)
    # Replace dots and other invalid chars with underscores
    safe_object_id = object_id.replace(".", "_").replace("-", "_")
    safe_method_name = method_sig.name.replace(".", "_").replace("-", "_")
    function_name = f"{safe_object_id}__{safe_method_name}"

    # Build parameters schema
    properties = {}
    required = []

    for param in method_sig.parameters:
        # Skip 'self' parameter
        if param.name == "self":
            continue

        param_schema = {
            "type": _python_type_to_json_schema(param.type),
            "description": param.description or f"Parameter {param.name}",
        }

        properties[param.name] = param_schema

        # Add to required if no default value
        if not param.has_default:
            required.append(param.name)

    return {
        "type": "function",
        "function": {
            "name": function_name,
            "description": method_sig.description or f"Call {object_type} {object_id}.{method_sig.name}",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def generate_resource_schemas(resources: list[ResourceProtocol]) -> list[dict]:
    """Generate tool schemas for all resources.

    Args:
        resources: List of resource instances

    Returns:
        List of OpenAI-compatible tool schemas
    """
    schemas = []

    for resource in resources:
        resource_id = resource.object_id

        # Get all @tool_use decorated methods
        tool_methods = Misc.extract_tool_use_methods(resource)

        for method_name, method in tool_methods:
            # Parse the method signature
            method_sig = Misc.parse_method_signature(method, object_id=resource_id)

            # Convert to schema
            schema = _method_signature_to_schema(
                method_sig,
                object_id=resource_id,
                object_type="resource",
            )
            schemas.append(schema)

    return schemas


def generate_workflow_schemas(workflows: list[WorkflowProtocol]) -> list[dict]:
    """Generate tool schemas for all workflows.

    Workflows have a default 'execute' method.

    Args:
        workflows: List of workflow instances

    Returns:
        List of OpenAI-compatible tool schemas
    """
    schemas = []

    for workflow in workflows:
        workflow_id = workflow.object_id

        # Workflows have execute as their primary method
        # Check if execute exists and get its signature
        if hasattr(workflow, "execute"):
            method = workflow.execute
            method_sig = Misc.parse_method_signature(method, object_id=workflow_id)

            schema = _method_signature_to_schema(
                method_sig,
                object_id=workflow_id,
                object_type="workflow",
            )
            schemas.append(schema)

    return schemas


def generate_tool_schemas(
    agents: list[AgentProtocol] | None = None,
    resources: list[ResourceProtocol] | None = None,
    workflows: list[WorkflowProtocol] | None = None,
) -> list[dict]:
    """Generate OpenAI-compatible tool schemas for all available tools.

    Args:
        agents: List of sub-agents (future: could generate schemas for agent.query)
        resources: List of resources to generate schemas for
        workflows: List of workflows to generate schemas for

    Returns:
        List of OpenAI-compatible tool schemas
    """
    schemas = []

    if resources:
        schemas.extend(generate_resource_schemas(resources))

    if workflows:
        schemas.extend(generate_workflow_schemas(workflows))

    # Future: Add agent schemas if needed
    # if agents:
    #     schemas.extend(generate_agent_schemas(agents))

    return schemas
