"""
ToolExecutor — implements ToolExecutorProtocol.

Orchestrates batch tool execution (sync and async), delegates single-call
dispatch to internal helpers, and holds the hook/approval infrastructure
for future phases.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import traceback
from typing import Any

import structlog

from dana.common.observable import observable
from dana.common.utils.misc import Misc
from dana.core.tool.tool_executor_helpers import (
    create_tool_error,
    create_tool_success,
    find_object_by_class_name,
    find_object_by_id,
    get_available_class_names,
    parse_function_name,
    validate_and_cast_method_arguments,
)


logger = structlog.get_logger()


class ToolExecutor:
    """Executes tool calls on behalf of an agent (sync and async).

    Implements ToolExecutorProtocol.

    Constructor args:
        hooks:                    List of ToolHookProtocol instances (Phase 7+).
        approval:                 ApprovalProtocol instance (Phase 7+).
        agent_getter:             Callable[[], agent] — returns the current agent
                                  (used only when caller does not pass agent directly).
        tool_name_registry_getter: Callable[[], dict] — returns the @named_tool registry
                                  maintained on AgentRuntime.
    """

    def __init__(
        self,
        hooks: list | None = None,
        approval: Any | None = None,
        agent_getter: Callable[[], Any] | None = None,
        tool_name_registry_getter: Callable[[], dict[str, tuple[Any, str]]] | None = None,
        max_workers: int | None = None,
    ) -> None:
        self._hooks = hooks or []
        self._approval = approval
        self._agent_getter = agent_getter
        self._tool_name_registry_getter = tool_name_registry_getter
        self._max_workers = max_workers

    # ------------------------------------------------------------------
    # Public API — ToolExecutorProtocol
    # ------------------------------------------------------------------

    @observable
    def execute_tools(
        self,
        agent: Any,
        tool_calls: list[dict[str, Any]],
        parallel: bool = False,
    ) -> list[dict[str, Any]]:
        """Sync batch executor — sequential by default, parallel via ThreadPoolExecutor when parallel=True."""
        if parallel:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                futures = [executor.submit(self._execute_single_call, agent, call) for call in tool_calls]
                results = [f.result() for f in futures]
        else:
            results = []
            for call in tool_calls:
                results.append(self._execute_single_call(agent, call))

        for result, call in zip(results, tool_calls, strict=False):
            if "tool_call_id" in call:
                result["tool_call_id"] = call["tool_call_id"]
        return results

    @observable
    async def execute_tools_async(self, agent: Any, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Async batch executor — runs all tool calls concurrently via asyncio.gather."""
        results = await asyncio.gather(*[self._execute_single_call_async(agent, call) for call in tool_calls])
        for result, call in zip(results, tool_calls, strict=False):
            if "tool_call_id" in call:
                result["tool_call_id"] = call["tool_call_id"]
        return list(results)

    # ------------------------------------------------------------------
    # Single-call dispatch (sync)
    # ------------------------------------------------------------------

    @observable
    def _execute_single_call(self, agent: Any, tool_call: dict[str, Any]) -> dict[str, Any]:
        """Dispatch one tool call synchronously."""
        function_name = tool_call.get("function", "")
        arguments = tool_call.get("arguments", {})
        registry = self._get_registry()

        # --- @named_tool registry fast path ---
        if function_name in registry:
            obj, method_name = registry[function_name]
            method = getattr(obj, method_name)
            try:
                arguments = validate_and_cast_method_arguments(method, arguments)
                if asyncio.iscoroutinefunction(method):
                    result = Misc.safe_asyncio_run(method, **arguments)
                else:
                    result = method(**arguments)
                return create_tool_success("resource", function_name, result)
            except Exception as exc:
                return create_tool_error(
                    "execution_error",
                    function_name,
                    f"Error executing call {function_name}: {exc}\n{traceback.format_exc()}",
                )

        # --- Standard name parsing fallback ---
        parsed = parse_function_name(function_name)
        if not parsed:
            return create_tool_error("format_error", function_name, "Expected ClassName:methodName or object_id__method format")

        identifier, method_name = parsed
        obj_info = find_object_by_id(agent, identifier) or find_object_by_class_name(agent, identifier)
        if not obj_info:
            available = get_available_class_names(agent)
            return create_tool_error(
                "class_not_found",
                identifier,
                "Object not found by object_id or class_name. Available classes: "
                + ", ".join(available[:10])
                + ("..." if len(available) > 10 else ""),
            )

        if hasattr(obj_info["object"], method_name):
            method = getattr(obj_info["object"], method_name)
            try:
                arguments = validate_and_cast_method_arguments(method, arguments)
                # Inject session_id for agent calls
                if obj_info["type"] == "agent":
                    arguments = self._inject_session_id(agent, arguments)
                if asyncio.iscoroutinefunction(method):
                    result = Misc.safe_asyncio_run(method, **arguments)
                else:
                    result = method(**arguments)
                return create_tool_success(obj_info["type"], f"{identifier}.{method_name}", result)
            except Exception as exc:
                return create_tool_error(
                    "execution_error",
                    f"{identifier}.{method_name}",
                    f"Error executing call {identifier}.{method_name}: {exc}\n{traceback.format_exc()}",
                )

        return create_tool_error(
            "method_not_found",
            f"{identifier}.{method_name}",
            f"Method '{method_name}' not found in object '{identifier}'\n{traceback.format_exc()}",
        )

    # ------------------------------------------------------------------
    # Single-call dispatch (async)
    # ------------------------------------------------------------------

    @observable
    async def _execute_single_call_async(self, agent: Any, tool_call: dict[str, Any]) -> dict[str, Any]:
        """Dispatch one tool call asynchronously."""
        function_name = tool_call.get("function", "")
        arguments = tool_call.get("arguments", {})
        registry = self._get_registry()

        # --- @named_tool registry fast path ---
        if function_name in registry:
            obj, method_name = registry[function_name]
            method = getattr(obj, method_name)
            try:
                arguments = validate_and_cast_method_arguments(method, arguments)
                if asyncio.iscoroutinefunction(method):
                    result = await method(**arguments)
                else:
                    result = method(**arguments)
                return create_tool_success("resource", function_name, result)
            except Exception as exc:
                return create_tool_error(
                    "execution_error",
                    function_name,
                    f"Error executing call {function_name}: {exc}\n{traceback.format_exc()}",
                )

        # --- Standard name parsing fallback ---
        parsed = parse_function_name(function_name)
        if not parsed:
            return create_tool_error("format_error", function_name, "Expected ClassName:methodName or object_id__method format")

        identifier, method_name = parsed
        obj_info = find_object_by_id(agent, identifier) or find_object_by_class_name(agent, identifier)
        if not obj_info:
            available = get_available_class_names(agent)
            return create_tool_error(
                "class_not_found",
                identifier,
                "Object not found by object_id or class_name. Available classes: "
                + ", ".join(available[:10])
                + ("..." if len(available) > 10 else ""),
            )

        # For async agent calls, prefer aquery over query
        actual_method_name = method_name
        if obj_info["type"] == "agent" and method_name == "query":
            actual_method_name = "aquery"

        if hasattr(obj_info["object"], actual_method_name):
            method = getattr(obj_info["object"], actual_method_name)
            try:
                arguments = validate_and_cast_method_arguments(method, arguments)
                if obj_info["type"] == "agent":
                    arguments = self._inject_session_id(agent, arguments)
                if asyncio.iscoroutinefunction(method):
                    result = await method(**arguments)
                else:
                    result = method(**arguments)
                return create_tool_success(obj_info["type"], f"{identifier}.{actual_method_name}", result)
            except Exception as exc:
                return create_tool_error(
                    "execution_error",
                    f"{identifier}.{actual_method_name}",
                    f"Error executing call {identifier}.{actual_method_name}: {exc}\n{traceback.format_exc()}",
                )

        return create_tool_error(
            "method_not_found",
            f"{identifier}.{actual_method_name}",
            f"Method '{actual_method_name}' not found in object '{identifier}'\n{traceback.format_exc()}",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_registry(self) -> dict[str, tuple[Any, str]]:
        """Return the @named_tool registry, or empty dict if not wired."""
        if self._tool_name_registry_getter is not None:
            return self._tool_name_registry_getter()
        return {}

    def _inject_session_id(self, agent: Any, arguments: dict[str, Any]) -> dict[str, Any]:
        """Inject session_id into arguments when the calling agent has an active event log."""
        if hasattr(agent, "_event_log") and agent._event_log is not None:
            session_id = agent._event_log._current_session_id
            if session_id is not None:
                arguments = dict(arguments)
                arguments["session_id"] = session_id
        return arguments
