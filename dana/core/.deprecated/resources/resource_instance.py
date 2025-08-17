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
from dana.registry import STRUCT_FUNCTION_REGISTRY


@dataclass
class ResourceType(StructType):
    """Runtime representation of a resource type definition.

    Behaves like a StructType but marks the type as a Resource for
    downstream runtime decisions (e.g., instantiation returns ResourceInstance).
    """

    def __repr__(self) -> str:
        """String representation showing this is a ResourceType."""
        field_strs = [f"{name}: {type_name}" for name, type_name in self.fields.items()]
        return f"ResourceType({self.name}, fields=[{', '.join(field_strs)}])"

    def __str__(self) -> str:
        """String representation showing this is a ResourceType."""
        return self.__repr__()


class ResourceInstance(StructInstance):
    """Runtime representation of a resource instance.

    Extends StructInstance semantics while providing a distinct runtime type
    for resource instances to enable feature gating and specialization.

    Can optionally wrap a backend implementation (BaseSysResource) for
    system-level resources like LLM, MCP, etc.
    """

    def __init__(self, struct_type: StructType, values: dict[str, Any] | None = None):
        """Initialize ResourceInstance with optional backend."""
        super().__init__(struct_type, values)
        self._backend: Any = None  # Will hold BaseSysResource if needed

    def set_backend(self, backend: Any) -> None:
        """Attach a backend implementation (typically BaseSysResource)."""
        self._backend = backend

    def __repr__(self) -> str:
        """String representation showing resource type and field values."""
        field_strs = []
        for field_name in self._type.field_order:
            value = self._values.get(field_name)
            field_strs.append(f"{field_name}={repr(value)}")

        return f"{self._type.name}({', '.join(field_strs)})"

    def __str__(self) -> str:
        """String representation showing resource type and field values."""
        return self.__repr__()

    # --- Default lifecycle methods ---
    # These delegate to struct-defined functions when present. If not present,
    # they behave as no-ops returning True, so resources always support the API.

    def start(self) -> bool | Any:
        """Start the resource by delegating to backend or struct-defined start().

        Priority:
        1. Backend initialize() if present
        2. Struct-defined start() method
        3. Return True (no-op)
        """
        # Try backend first
        if self._backend:
            if hasattr(self._backend, "initialize"):
                # Handle both sync and async initialize
                import inspect

                if inspect.iscoroutinefunction(self._backend.initialize):
                    # Async initialize - return the coroutine for caller to await
                    return self._backend.initialize()
                else:
                    # Sync initialize
                    return self._backend.initialize()
            elif hasattr(self._backend, "start"):
                return self._backend.start()

        # Fall back to struct method
        try:
            return self.call_method("start")
        except AttributeError:
            return True

    def stop(self) -> bool | Any:
        """Stop the resource by delegating to backend or struct-defined stop().

        Priority:
        1. Backend cleanup() if present
        2. Struct-defined stop() method
        3. Return True (no-op)
        """
        # Try backend first
        if self._backend:
            if hasattr(self._backend, "cleanup"):
                # Handle both sync and async cleanup
                import inspect

                if inspect.iscoroutinefunction(self._backend.cleanup):
                    # Async cleanup - return the coroutine for caller to await
                    return self._backend.cleanup()
                else:
                    # Sync cleanup
                    return self._backend.cleanup()
            elif hasattr(self._backend, "stop"):
                return self._backend.stop()

        # Fall back to struct method
        try:
            return self.call_method("stop")
        except AttributeError:
            return True

    def query(self, request: Any) -> Any:
        """Query the resource through backend or struct-defined query().

        Priority:
        1. Backend query() if present
        2. Struct-defined query() method
        3. Return error response
        """
        # Try backend first
        if self._backend and hasattr(self._backend, "query"):
            return self._backend.query(request)

        # Try struct method
        try:
            return self.call_method("query", request)
        except AttributeError:
            # No query method available
            from dana.common.types import BaseResponse

            return BaseResponse(success=False, error=f"Resource {self._type.name} does not support query operations")

    def call_method(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call a method on the resource instance.

        First checks MethodRegistry, then falls back to parent implementation.
        """
        # Check MethodRegistry first
        # method_key = (self._type.name, method_name)
        method = STRUCT_FUNCTION_REGISTRY.lookup_method(self._type.name, method_name)

        if method:
            # Call the registered method
            return method(self, *args, **kwargs)

        # Fall back to parent implementation
        return super().call_method(method_name, *args, **kwargs)

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

    Mirrors create_struct_type_from_ast but accepts ResourceDefinition and handles inheritance.

    Args:
        resource_def: The ResourceDefinition AST node
        context: Optional sandbox context for evaluating default values

    Returns:
        ResourceType with fields and default values, including inherited fields
    """
    # Import here to avoid circular imports
    from dana.core.lang.ast import ResourceDefinition

    if not isinstance(resource_def, ResourceDefinition):
        raise TypeError(f"Expected ResourceDefinition, got {type(resource_def)}")

    # Start with inherited fields if parent exists
    fields: dict[str, str] = {}
    field_order: list[str] = []
    field_defaults: dict[str, Any] = {}
    field_comments: dict[str, str] = {}

    # Handle inheritance by merging parent fields
    if resource_def.parent_name:
        # Get parent from the global registry
        from dana.registry import STRUCT_FUNCTION_REGISTRY

        parent_type = STRUCT_FUNCTION_REGISTRY.get_type(resource_def.parent_name)
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
            field_comments[field.name] = cast(str, field.comment)

    return ResourceType(
        name=resource_def.name,
        fields=fields,
        field_order=field_order,
        field_defaults=field_defaults if field_defaults else None,
        field_comments=field_comments,
        docstring=resource_def.docstring,
    )
