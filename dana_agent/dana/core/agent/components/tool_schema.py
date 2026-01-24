"""
Tool Schema Generator for Native Function Calling

Generates OpenAI-compatible tool schemas from DANA resources and workflows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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


def _python_type_to_json_schema(python_type: str) -> dict:
    """Convert Python type string to JSON Schema.

    Args:
        python_type: Python type string (e.g., "str", "list[str]", "dict[str, Any]")

    Returns:
        JSON Schema dict with type and optional items/additionalProperties
    """
    # Handle common type variations
    base_type = python_type.split("[")[0].strip()  # Get base type before generics
    base_type_clean = base_type.replace("Optional[", "").replace("]", "")

    json_type = PYTHON_TO_JSON_TYPE.get(base_type_clean, "string")

    # For arrays, extract item type from generics like list[str], list[dict], etc.
    if json_type == "array":
        # Try to extract the item type from list[X]
        if "[" in python_type and "]" in python_type:
            inner_start = python_type.index("[") + 1
            inner_end = python_type.rindex("]")
            inner_type = python_type[inner_start:inner_end].strip()
            # Recursively get schema for inner type
            inner_schema = _python_type_to_json_schema(inner_type)
            return {"type": "array", "items": inner_schema}
        else:
            # Default to string items if no generic type specified
            return {"type": "array", "items": {"type": "string"}}

    # For objects (dict), add additionalProperties for flexibility
    if json_type == "object":
        return {"type": "object", "additionalProperties": True}

    return {"type": json_type}


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

        # Get base schema from type (may include items for arrays, etc.)
        param_schema = _python_type_to_json_schema(param.type)
        # Add description
        param_schema["description"] = param.description or f"Parameter {param.name}"

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

        for _method_name, method in tool_methods:
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


def generate_agent_schemas(agents: list[AgentProtocol]) -> list[dict]:
    """Generate tool schemas for sub-agents.

    Each agent is exposed as a single tool with a `query` method that accepts
    a message parameter. The agent's public_description is used as the tool
    description so the LLM knows what the agent can do.

    Args:
        agents: List of agent instances to generate schemas for

    Returns:
        List of OpenAI-compatible tool schemas
    """
    schemas = []

    for agent in agents:
        # Use agent_type as the tool identifier (more readable than object_id)
        agent_id = agent.agent_type
        safe_agent_id = agent_id.replace(".", "_").replace("-", "_")
        function_name = f"{safe_agent_id}__query"

        # Get the agent's description for the LLM
        description = getattr(agent, "public_description", None)
        if not description:
            description = f"Send a task to the {agent_id} agent and receive a result."

        schema = {
            "type": "function",
            "function": {
                "name": function_name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The task or question to send to this agent",
                        },
                    },
                    "required": ["message"],
                },
            },
        }
        schemas.append(schema)

    return schemas


def generate_tool_schemas(
    agents: list[AgentProtocol] | None = None,
    resources: list[ResourceProtocol] | None = None,
    workflows: list[WorkflowProtocol] | None = None,
) -> list[dict]:
    """Generate OpenAI-compatible tool schemas for all available tools.

    Args:
        agents: List of sub-agents to generate schemas for
        resources: List of resources to generate schemas for
        workflows: List of workflows to generate schemas for

    Returns:
        List of OpenAI-compatible tool schemas (deduplicated by function name)
    """
    schemas = []
    seen_names: set[str] = set()

    # Add agent schemas first (they're high-level delegation tools)
    if agents:
        for schema in generate_agent_schemas(agents):
            func_name = schema["function"]["name"]
            if func_name not in seen_names:
                schemas.append(schema)
                seen_names.add(func_name)

    if resources:
        for schema in generate_resource_schemas(resources):
            func_name = schema["function"]["name"]
            if func_name not in seen_names:
                schemas.append(schema)
                seen_names.add(func_name)

    if workflows:
        for schema in generate_workflow_schemas(workflows):
            func_name = schema["function"]["name"]
            if func_name not in seen_names:
                schemas.append(schema)
                seen_names.add(func_name)

    return schemas
