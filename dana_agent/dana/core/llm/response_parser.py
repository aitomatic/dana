"""
JSONResponseParser — parses raw LLM responses into structured ParsedResponse objects.

Extracted from AgentRuntime.parse_response so the parsing logic lives in one place
and can be tested independently. parse_response() accepts an LLMResponse directly,
eliminating the need for the old _last_llm_response stash.
"""

from __future__ import annotations

from collections.abc import Callable
import json
import re
from typing import Any

import structlog

from dana.common.llm.types import LLMResponse
from dana.core.runtime.protocols import ParsedResponse, TodoItem


logger = structlog.get_logger()


class JSONResponseParser:
    """
    Parses LLM responses (JSON-based protocol) into ParsedResponse.

    Args:
        get_native_tools: Callable returning the current native-tools list (or None).
            Passed as a lambda so the parser always reads the up-to-date value even
            though _native_tools is set after AgentRuntime.__init__.
    """

    def __init__(self, get_native_tools: Callable[[], list | None]) -> None:
        self._get_native_tools = get_native_tools

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_response(self, response: LLMResponse) -> ParsedResponse:
        """Parse a full LLMResponse into a structured ParsedResponse."""
        native_tools = self._get_native_tools()

        if response is None:
            return ParsedResponse(done=None, reasoning=None, response=None, tool_calls=[], todo_list=None)

        content = (str(response.content).strip()) if response.content else ""
        done = None
        response_text = None
        tool_calls: list[dict[str, Any]] = []
        todo_list: list[TodoItem] | None = None
        reasoning = None

        # Check for native tool calls from the LLM response
        has_native_tool_calls = False
        if response.tool_calls:
            tool_calls.extend(_to_tool_call_dicts(response.tool_calls))
            has_native_tool_calls = True

        # Parse JSON from content
        if content:
            parsed_json = _extract_json(content)
            if parsed_json:
                reasoning = parsed_json.get("reasoning")
                json_todo_list = parsed_json.get("todo_list", [])
                if json_todo_list:
                    todo_list = []
                    for item in json_todo_list:
                        if isinstance(item, dict):
                            todo_list.append(
                                TodoItem(
                                    content=item.get("content", ""),
                                    status=item.get("status", "pending"),
                                )
                            )
                done = parsed_json.get("done")
                # Accept both "response" and "message" as valid field names
                response_text = parsed_json.get("response") or parsed_json.get("message")

                # Ensure response_text is a string (LLM might return nested dict)
                if response_text is not None and not isinstance(response_text, str):
                    response_text = str(response_text)

                # Handle case where response text comes after a minimal JSON object
                # e.g., '{"done":true} Here is the actual response...'
                if not response_text and done is True:
                    trailing_text = _extract_trailing_text(content)
                    if trailing_text:
                        response_text = trailing_text

                # Only extract tool_calls from JSON if not using native tools
                if not native_tools:
                    json_tool_calls = parsed_json.get("tool_calls", [])
                    if json_tool_calls:
                        for tc in json_tool_calls:
                            name = tc.get("name", "")
                            params = tc.get("parameters", {})
                            tool_calls.append({"function": name, "arguments": params})
            elif not has_native_tool_calls:
                if not native_tools:
                    logger.warning(
                        "Failed to parse JSON from LLM response",
                        content_preview=content[:500] if len(content) > 500 else content,
                    )

        # Native tool calls override done flag
        if has_native_tool_calls:
            done = False

        return ParsedResponse(
            done=done,
            reasoning=reasoning,
            response=response_text if response_text else None,
            tool_calls=tool_calls,
            todo_list=todo_list,
        )

    def validate_done_output(self, done: bool | None, has_tool_calls: bool, has_response: bool) -> str:
        """Validate the output format and return the next action."""
        if done is None:
            return "retry"
        if done and has_tool_calls:
            return "retry"
        if not done and has_response:
            return "retry"
        if not done and not has_tool_calls:
            return "retry"
        if done and not has_response:
            return "retry"
        return "exit" if done else "continue"


# ---------------------------------------------------------------------------
# Module-level helpers (pure functions, no state)
# ---------------------------------------------------------------------------


def _to_tool_call_dicts(llm_tool_calls: list) -> list[dict[str, Any]]:
    """Convert native LLM tool call objects to our standard dict format."""
    tool_call_dicts = []
    for llm_tool_call in llm_tool_calls:
        try:
            tool_call_id = getattr(llm_tool_call, "id", None)
            function_name = llm_tool_call.function.name
            arguments = llm_tool_call.function.arguments
            if isinstance(arguments, str):
                arguments = json.loads(arguments) if arguments else {}
            call_dict = {"function": function_name, "arguments": arguments}
            if tool_call_id:
                call_dict["tool_call_id"] = tool_call_id
            tool_call_dicts.append(call_dict)
        except Exception:
            continue
    return tool_call_dicts


def _extract_json(content: str) -> dict[str, Any] | None:
    """Extract JSON object from content string."""
    if not content:
        return None

    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    json_match = re.search(r"```(?:json)?\s*(\{.+\})\s*```", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try balanced brace matching
    start_idx = content.find('{"done"')
    if start_idx == -1:
        start_idx = content.find("{\n")
    if start_idx == -1:
        start_idx = content.find("{")

    if start_idx != -1:
        depth = 0
        for i, char in enumerate(content[start_idx:], start_idx):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(content[start_idx : i + 1])
                    except json.JSONDecodeError:
                        pass
                    break

    return None


def _extract_trailing_text(content: str) -> str | None:
    """Extract text that comes after a JSON object.

    Handles cases like: '{"done":true} Here is the actual response...'
    """
    if not content:
        return None

    start_idx = content.find("{")
    if start_idx == -1:
        return None

    depth = 0
    end_idx = -1
    for i, char in enumerate(content[start_idx:], start_idx):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end_idx = i
                break

    if end_idx == -1:
        return None

    trailing = content[end_idx + 1 :].strip()
    return trailing if trailing else None
