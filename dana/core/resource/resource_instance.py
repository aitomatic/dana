"""
Resource Type System for Dana

Defines first-class resource runtime types that extend the core struct system.
Mirrors the structure of dana/agent/agent_instance.py for consistency.
"""

import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Any, cast

from dana.core.lang.interpreter.struct_system import StructInstance, StructType


@dataclass
class ResourceType(StructType):
    """Runtime representation of a resource type definition.

    Behaves like a StructType but marks the type as a Resource for
    downstream runtime decisions (e.g., instantiation returns ResourceInstance).
    """


class ResourceInstance(StructInstance):
    """Runtime representation of a resource instance.

    Extends StructInstance semantics while providing a distinct runtime type
    for resource instances to enable feature gating and specialization.
    """

    # --- Default lifecycle methods ---
    # These delegate to struct-defined functions when present. If not present,
    # they behave as no-ops returning True, so resources always support the API.

    def start(self) -> bool | Any:
        """Start the resource by delegating to struct-defined start(), if any.

        Returns True if no explicit start is defined.
        """
        try:
            return self.call_method("start")
        except AttributeError:
            return True

    def stop(self) -> bool | Any:
        """Stop the resource by delegating to struct-defined stop(), if any.

        Returns True if no explicit stop is defined.
        """
        try:
            return self.call_method("stop")
        except AttributeError:
            return True

    # --- Context manager support ---
    # Sync context manager calls start()/stop().
    def __enter__(self) -> "ResourceInstance":
        try:
            result = self.start()
            # Support start() returning an awaitable even in sync path (ignore result)
            if isinstance(result, Awaitable):
                # Best-effort: run to completion
                try:
                    asyncio.get_event_loop().run_until_complete(result)  # type: ignore[arg-type]
                except RuntimeError:
                    # No running loop; start() will be effectively deferred
                    pass
        except Exception:
            # Suppress start errors here; user code may handle within context
            pass
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            result = self.stop()
            if isinstance(result, Awaitable):
                try:
                    asyncio.get_event_loop().run_until_complete(result)  # type: ignore[arg-type]
                except RuntimeError:
                    pass
        except Exception:
            pass
        # Do not suppress exceptions from the with-block
        return False

    # Async context manager calls start()/stop(), awaiting if coroutine.
    async def __aenter__(self) -> "ResourceInstance":
        try:
            result = self.start()
            if asyncio.iscoroutine(result) or isinstance(result, Awaitable):
                await result  # type: ignore[misc]
        except Exception:
            pass
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        try:
            result = self.stop()
            if asyncio.iscoroutine(result) or isinstance(result, Awaitable):
                await result  # type: ignore[misc]
        except Exception:
            pass
        return False


def create_resource_type_from_ast(resource_def, context=None) -> ResourceType:
    """Create a ResourceType from a ResourceDefinition AST node.

    Mirrors create_struct_type_from_ast but accepts ResourceDefinition.

    Args:
        resource_def: The ResourceDefinition AST node
        context: Optional sandbox context for evaluating default values

    Returns:
        ResourceType with fields and default values
    """
    # Import here to avoid circular imports
    from dana.core.lang.ast import ResourceDefinition

    if not isinstance(resource_def, ResourceDefinition):
        raise TypeError(f"Expected ResourceDefinition, got {type(resource_def)}")

    # Convert ResourceField list to dict and field order
    fields: dict[str, str] = {}
    field_order: list[str] = []
    field_defaults: dict[str, Any] = {}
    field_comments: dict[str, str] = {}

    for field in resource_def.fields:
        if field.type_hint is None:
            raise ValueError(f"Field {field.name} has no type hint")
        if not hasattr(field.type_hint, "name"):
            raise ValueError(f"Field {field.name} type hint {field.type_hint} has no name attribute")
        fields[field.name] = field.type_hint.name
        field_order.append(field.name)

        if field.default_value is not None:
            field_defaults[field.name] = field.default_value

        if getattr(field, "comment", None):
            field_comments[field.name] = cast(str, field.comment)

    return ResourceType(
        name=resource_def.name,
        fields=fields,
        field_order=field_order,
        field_defaults=field_defaults if field_defaults else None,
        field_comments=field_comments,
        docstring=resource_def.docstring,
    )
