"""
Helper functions for ToolExecutor — pure module-level functions with no state.

Extracted from AgentRuntime to keep ToolExecutor focused on orchestration.
Helpers handle: function name parsing, object lookup, argument validation,
and result formatting.
"""

from __future__ import annotations

import json
import types
from typing import TYPE_CHECKING, Any, Union, get_origin

from dana.common.utils.misc import Misc


if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Namespace class (for __init__.py re-export as ToolExecutorHelpers)
# ---------------------------------------------------------------------------


class ToolExecutorHelpers:
    """Namespace re-export — all public helpers are module-level functions above."""


# ---------------------------------------------------------------------------
# Function name parsing
# ---------------------------------------------------------------------------


def parse_function_name(function_name: str) -> tuple[str, str] | None:
    """Parse function name into (identifier, method_name).

    Supports two formats:
      - "ClassName:method"      → ("ClassName", "method")
      - "object_id__method"     → ("object-id", "method")
    Returns None if neither format matches.
    """
    if ":" in function_name:
        return tuple(function_name.split(":", 1))  # type: ignore[return-value]
    if "__" in function_name:
        parts = function_name.rsplit("__", 1)
        if len(parts) == 2:
            return parts[0].replace("_", "-"), parts[1]
    return None


# ---------------------------------------------------------------------------
# Object lookup
# ---------------------------------------------------------------------------


def find_object_by_id(agent: Any, object_id: str) -> dict[str, Any] | None:
    """Find an agent/resource/workflow on `agent` by object_id.

    Also falls back to the global registry if not found locally.
    """
    for sub_agent in agent.available_agents:
        if (hasattr(sub_agent, "object_id") and sub_agent.object_id == object_id) or (
            hasattr(sub_agent, "agent_type") and sub_agent.agent_type == object_id
        ):
            return {"type": "agent", "object": sub_agent}

    for resource in agent.available_resources:
        if (hasattr(resource, "object_id") and resource.object_id == object_id) or (
            hasattr(resource, "resource_id") and resource.resource_id == object_id
        ):
            return {"type": "resource", "object": resource}

    for workflow in agent.available_workflows:
        if (hasattr(workflow, "object_id") and workflow.object_id == object_id) or (
            hasattr(workflow, "workflow_id") and workflow.workflow_id == object_id
        ):
            return {"type": "workflow", "object": workflow}

    # Fallback: global registry
    agent.ensure_registered()
    registry = agent._registry
    if registry and object_id in registry._items:
        found = registry.get(object_id)
        if found:
            return {"type": "agent", "object": found}

    return None


def find_object_by_class_name(agent: Any, class_name: str) -> dict[str, Any] | None:
    """Find an agent/resource/workflow on `agent` by class name."""
    for sub_agent in agent.available_agents:
        if sub_agent.__class__.__name__ == class_name:
            return {"type": "agent", "object": sub_agent}

    for resource in agent.available_resources:
        if resource.__class__.__name__ == class_name:
            return {"type": "resource", "object": resource}

    for workflow in agent.available_workflows:
        if workflow.__class__.__name__ == class_name:
            return {"type": "workflow", "object": workflow}

    return None


def get_available_class_names(agent: Any) -> list[str]:
    """Return list of class names for all components attached to agent."""
    classes = []
    for sub_agent in agent.available_agents:
        classes.append(sub_agent.__class__.__name__)
    for resource in agent.available_resources:
        classes.append(resource.__class__.__name__)
    for workflow in agent.available_workflows:
        classes.append(workflow.__class__.__name__)
    return classes


# ---------------------------------------------------------------------------
# Argument validation / type coercion
# ---------------------------------------------------------------------------


def validate_and_cast_method_arguments(method: Any, arguments: dict[str, Any]) -> dict[str, Any]:
    """Coerce LLM-supplied arguments to the types declared in *method*'s signature.

    LLMs often return all values as strings; this casts them to int/float/bool/list/dict
    where the method signature indicates a different type.
    Also strips empty/whitespace-only keys that LLMs sometimes generate.
    """
    # Strip empty or whitespace-only keys that LLMs sometimes generate
    arguments = {k: v for k, v in arguments.items() if k and k.strip()}

    try:
        signature = Misc.parse_method_signature(method)
    except Exception:
        return arguments

    for param in signature.parameters:
        if not (param.type_object and param.name in arguments):
            continue
        if param.type_object is Any:
            continue

        origin = get_origin(param.type_object)
        if origin is None:
            origin = param.type_object

        is_union_type = hasattr(param.type_object, "__args__") and (origin is Union or origin is types.UnionType)
        hinted_types = param.type_object.__args__ if is_union_type else [origin]

        for hinted_type in hinted_types:
            if hinted_type is type(None):
                continue
            if hinted_type is Any:
                break

            type_origin = get_origin(hinted_type)
            if type_origin is None:
                type_origin = hinted_type

            if type_origin is not Any and isinstance(arguments[param.name], type_origin):
                break

            if type_origin in (str, int, float):
                try:
                    arguments[param.name] = type_origin(arguments[param.name])
                    break
                except Exception:
                    continue
            elif type_origin is bool:
                val = arguments[param.name]
                if isinstance(val, bool):
                    break
                if isinstance(val, str):
                    arguments[param.name] = val.lower() in ("true", "1", "yes", "on")
                    break
                try:
                    arguments[param.name] = bool(val)
                    break
                except Exception:
                    continue
            elif type_origin is list:
                val = arguments[param.name]
                if isinstance(val, list):
                    break
                if isinstance(val, str):
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, list):
                            arguments[param.name] = parsed
                            break
                    except (json.JSONDecodeError, ValueError):
                        continue
            elif type_origin is dict:
                val = arguments[param.name]
                if isinstance(val, dict):
                    break
                if isinstance(val, str):
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, dict):
                            arguments[param.name] = parsed
                            break
                    except (json.JSONDecodeError, ValueError):
                        continue

    return arguments


# ---------------------------------------------------------------------------
# Result formatting
# ---------------------------------------------------------------------------


def create_tool_success(tool_type: str, target: str, result: Any) -> dict[str, Any]:
    """Format a successful tool result."""
    return {"type": tool_type, "target": target, "result": result, "success": True}


def create_tool_error(tool_type: str, target: str, error_message: str) -> dict[str, Any]:
    """Format a failed tool result."""
    return {"type": tool_type, "target": target, "result": f"Error: {error_message}", "success": False}
