"""
Base runtime class with common logic and customization hooks.

This module provides BaseRuntime, which contains all the shared functionality
for agent runtimes. Subclasses override specific hooks to customize behavior
for different LLM providers.
"""

from __future__ import annotations

from abc import ABC
import asyncio
from dataclasses import dataclass
from datetime import datetime
import inspect
import json
import os
import re
import traceback
from typing import TYPE_CHECKING, Any

import structlog

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage, LLMResponse
from dana.common.observable import observable
from dana.common.protocols.types import LearningPhase
from dana.common.utils.misc import Misc
from dana.core.context import ContextBuilder


if TYPE_CHECKING:
    from dana.core.agent.timeline import Timeline

logger = structlog.get_logger()


@dataclass
class TodoItem:
    content: str
    status: str  # "pending", "in_progress", "completed"


@dataclass
class ParsedResponse:
    done: bool | None
    reasoning: str | None
    response: str | None
    tool_calls: list[dict[str, Any]]
    todo_list: list[TodoItem] | None = None


class AgentRuntime(ABC):
    """
    Agent runtime with common logic and customization hooks.

    Subclasses should override the hook methods to customize behavior:
    - get_system_prompt_template() - The main prompt template (has default implementation)
    - get_identity(agent) - How the agent describes itself
    - build_output_format_correction() - Message for invalid output
    - get_runtime_context_fields() - Which context fields to include
    - format_tool_for_prompt(signature) - How to format tool descriptions
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0,
        max_tokens: int | None = None,
        llm: LLM | None = None,
        provider: str = "anthropic",
        use_native_tools: bool | None = None,
    ):
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._llm = llm
        self._provider = provider
        self._agent = None
        self._native_tools = None
        self._use_native_tools = use_native_tools
        self._last_llm_response: LLMResponse | None = None

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def llm(self) -> LLM | None:
        return self._llm

    def set_llm(self, llm: LLM) -> None:
        self._llm = llm

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

    # -------------------------------------------------------------------------
    # Customization Hooks - Override these in subclasses
    # -------------------------------------------------------------------------

    def get_system_prompt_template(self, native_tools: bool) -> str:
        """Return the system prompt template.

        Default implementation returns SYSTEM_PROMPT_TEMPLATE_NATIVE_TOOLS or
        SYSTEM_PROMPT_TEMPLATE_JSON based on native_tools flag.
        Subclasses can override for custom behavior.

        Args:
            native_tools: Whether native tool calling is enabled.

        Returns:
            Template string with {{placeholders}} for substitution.
        """
        if native_tools:
            return self.SYSTEM_PROMPT_TEMPLATE_NATIVE_TOOLS
        return self.SYSTEM_PROMPT_TEMPLATE_JSON

    def get_identity(self, agent) -> str:
        """Return the agent's identity description.

        Override to customize how the agent describes itself.
        """
        return inspect.getdoc(agent.__class__) or f"{agent.agent_type} agent."

    def get_runtime_context_fields(self) -> list[str]:
        """Return which context fields to include.

        Override to customize what context is injected.
        Default: ["timestamp", "timezone", "location", "user"]
        """
        return ["timestamp", "timezone", "location", "user"]

    def format_tool_for_prompt(self, signature) -> str:
        """Format a tool signature for the prompt.

        Override to customize how tools are described.

        Args:
            signature: Parsed method signature from Misc.parse_method_signature()

        Returns:
            JSON string describing the tool.
        """
        identifier = signature.object_id or signature.class_name or "Unknown"
        tool_name = f"{identifier}:{signature.name}"

        params_schema = {}
        for p in signature.parameters:
            params_schema[p.name] = {
                "description": p.description,
                "required": not p.has_default,
            }
            if p.example:
                params_schema[p.name]["example"] = p.example

        tool_obj = {
            "name": tool_name,
            "description": signature.description,
            "parameters": params_schema,
        }

        return json.dumps(tool_obj)

    # -------------------------------------------------------------------------
    # Core Implementation - Usually don't need to override
    # -------------------------------------------------------------------------

    def public_description(self, agent) -> str:
        return self.get_identity(agent)

    def private_identity(self, agent) -> str:
        return f"I am a {agent.agent_type} agent with ID {agent.object_id}."

    def system_prompt(self, agent) -> str:
        return self._build_system_prompt(agent)

    @observable
    def build_prompt(self, agent, timeline: Timeline, learned_context: str | None = None) -> list[LLMMessage]:
        """Build LLM messages from timeline.

        Simple approach: system prompt + timeline messages in order.
        Learnings and retrieved context are added before the timeline.
        """
        self._agent = agent
        messages = []

        # Build native tools first (affects system prompt choice)
        self._build_native_tools_if_supported(agent)

        # Inject ephemeral runtime context
        runtime_context = self._get_runtime_context()
        if timeline:
            timeline.set_context(runtime_context)

        # Build system prompt with runtime context prepended
        system_prompt = self._build_system_prompt(agent)
        context_line = self._format_runtime_context(runtime_context)
        full_system_prompt = f"{context_line}\n\n{system_prompt}" if context_line else system_prompt
        messages.append(LLMMessage(role="system", content=full_system_prompt))

        if timeline:
            # Find the latest user message for context retrieval (learnings, ltmemory, etc.)
            task = self._get_latest_user_task(timeline)

            # Build retrieved context (learnings, ltmemory, resource queries)
            context_text = self._build_retrieved_context(agent, timeline, task, learned_context)

            # Add retrieved context as a user message if present
            if context_text:
                messages.append(LLMMessage(role="user", content=f"<CONTEXT>\n{context_text}\n</CONTEXT>"))

            # Add timeline messages in order - simple and straightforward
            timeline_messages = timeline.to_llm_messages()
            messages.extend(timeline_messages)

        self._log_prompt_build(agent, system_prompt, timeline, messages)

        return messages

    def _get_latest_user_task(self, timeline: Timeline) -> str:
        """Get the latest user message content for context retrieval."""
        from dana.core.agent.timeline import TimelineEntryType

        for entry in reversed(timeline.timeline):
            if entry.entry_type == TimelineEntryType.USER_MESSAGE:
                return entry.content
        return ""

    def _build_retrieved_context(self, agent, timeline: Timeline, task: str, learned_context: str | None) -> str:
        """Build retrieved context from learnings, ltmemory, and resources."""
        if not task:
            return ""

        context_parts = []

        # Add learned context if provided
        if learned_context:
            context_parts.append(learned_context)

        # Add learnings from learner
        learner = getattr(agent, "_learner", None)
        if learner is not None:
            related_acquisitive = learner.query_learnings(task, LearningPhase.ACQUISITIVE)
            if related_acquisitive:
                context_parts.append(f"Learning from the past: {related_acquisitive}")
            related_retentive = learner.query_learnings(task, LearningPhase.RETENTIVE)
            if related_retentive:
                context_parts.append(f"Relevant memories from past sessions: {related_retentive}")

        # Add context from ltmemory and resources
        class _TaggedQueryable:
            def __init__(self, source, tag: str):
                self._source = source
                self._tag = tag

            def query(self, question: str) -> str:
                result = self._source.query(question)
                return f"<{self._tag}>\n{result}\n</{self._tag}>"

        ctx = ContextBuilder(token_budget=getattr(timeline, "max_context_tokens", 100000))
        ltmemory = getattr(agent, "_ltmemory", None)
        if ltmemory is not None:
            ctx.add_source("ltmemory", _TaggedQueryable(ltmemory, "LTMEMORY"))

        for resource in getattr(agent, "_resources", []):
            if hasattr(resource, "query") and hasattr(resource, "resource_id"):
                ctx.add_source(resource.resource_id, _TaggedQueryable(resource, resource.resource_id.upper()))

        context = ctx.build(task=task)
        if context.text:
            context_parts.append(context.text)

        return "\n\n".join(context_parts) if context_parts else ""

    @observable
    def call_llm(self, messages: list[LLMMessage]) -> str:
        llm = self._resolve_llm()
        tools = self._native_tools if self._native_tools else None
        response = llm.chat_response_sync(
            messages,
            agent_id=self._agent.object_id if self._agent else None,
            agent_type=self._agent.agent_type if self._agent else None,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            tools=tools,
            json_mode=True,
        )
        self._last_llm_response = response
        return response.content

    @observable
    async def call_llm_async(self, messages: list[LLMMessage]) -> str:
        llm = self._resolve_llm()
        tools = self._native_tools if self._native_tools else None
        response = await llm.chat_response(
            messages,
            agent_id=self._agent.object_id if self._agent else None,
            agent_type=self._agent.agent_type if self._agent else None,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            tools=tools,
            json_mode=True,
        )
        self._last_llm_response = response
        return response.content

    @observable
    def parse_response(self, raw: str | dict | Any) -> ParsedResponse:
        if raw is None:
            return ParsedResponse(done=None, reasoning=None, response=None, tool_calls=[], todo_list=None)

        # Ensure raw is a string - LLM providers sometimes return unexpected types
        if not isinstance(raw, str):
            raw = str(raw)

        content = raw.strip()
        done = None
        response_text = None
        tool_calls: list[dict[str, Any]] = []
        todo_list: list[TodoItem] | None = None
        reasoning = None

        # Check for native tool calls from the LLM response
        has_native_tool_calls = False
        if self._last_llm_response and self._last_llm_response.tool_calls:
            tool_calls.extend(self._to_tool_call_dicts(self._last_llm_response.tool_calls))
            has_native_tool_calls = True

        # Parse JSON from content
        if content:
            parsed_json = self._extract_json(content)
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
                response_text = parsed_json.get("response")
                # Only extract tool_calls from JSON if not using native tools
                if not self._native_tools:
                    json_tool_calls = parsed_json.get("tool_calls", [])
                    if json_tool_calls:
                        for tc in json_tool_calls:
                            name = tc.get("name", "")
                            params = tc.get("parameters", {})
                            tool_calls.append({"function": name, "arguments": params})
            elif not has_native_tool_calls:
                if not self._native_tools:
                    logger.warning(
                        "Failed to parse JSON from LLM response", content_preview=content[:500] if len(content) > 500 else content
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

    @observable
    def execute_tools(self, agent, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self._agent = agent
        results = []
        for call in tool_calls:
            result = self._execute_single_call(call)
            if "tool_call_id" in call:
                result["tool_call_id"] = call["tool_call_id"]
            results.append(result)
        return results

    @observable
    async def execute_tools_async(self, agent, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self._agent = agent
        results = await asyncio.gather(*[self._execute_single_call_async(call) for call in tool_calls])
        for result, call in zip(results, tool_calls, strict=False):
            if "tool_call_id" in call:
                result["tool_call_id"] = call["tool_call_id"]
        return list(results)

    def build_output_format_correction(self) -> LLMMessage:
        """Build correction message for invalid output format.

        Override to customize the correction message for specific providers.
        """
        if self._native_tools:
            return LLMMessage(
                role="user",
                content=(
                    "ERROR: You returned done=false but did NOT call any tools.\n\n"
                    "You MUST do ONE of these:\n\n"
                    "A) If you need more data: USE THE FUNCTION CALLING FEATURE to call a tool RIGHT NOW.\n"
                    "   Do NOT just say you need to call a tool - actually invoke it!\n"
                    '   Then output: {"done": false, "reasoning": "Calling tool...", "response": null}\n\n'
                    "B) If you have enough data: Provide your final answer NOW.\n"
                    '   Output: {"done": true, "reasoning": "...", "response": "YOUR COMPLETE ANSWER HERE"}\n\n'
                    "Based on the conversation, you likely have enough information to answer.\n"
                    "PROVIDE YOUR ANSWER NOW using the data you have."
                ),
            )
        else:
            return LLMMessage(
                role="user",
                content=(
                    "Invalid format. Reply with ONLY valid JSON:\n\n"
                    "If you NEED more information, call a tool:\n"
                    '{"done": false, "reasoning": "...", "response": null, "tool_calls": [{"name": "...", "parameters": {...}}]}\n\n'
                    "If you HAVE all the information needed, provide your answer:\n"
                    '{"done": true, "reasoning": "...", "response": "your synthesized answer", "tool_calls": []}\n\n'
                    "RULES:\n"
                    "- done=false REQUIRES tool_calls\n"
                    "- done=true REQUIRES response"
                ),
            )

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _resolve_llm(self) -> LLM:
        if self._llm is not None:
            return self._llm
        if self._agent is not None and getattr(self._agent, "_llm_client", None) is not None:
            return self._agent.llm_client
        self._llm = LLM(provider=self._provider, model=self._model)
        if self._agent is not None:
            self._agent.llm_client = self._llm
        return self._llm

    _cached_location: dict[str, str] | None = None

    def _get_runtime_context(self) -> dict[str, Any]:
        """Get runtime context info for the current query."""
        fields = self.get_runtime_context_fields()
        context = {}

        now = datetime.now().astimezone()
        if "timestamp" in fields:
            context["timestamp"] = now.strftime("%Y-%m-%d %H:%M:%S")
        if "timezone" in fields:
            context["timezone"] = now.tzname() or "UTC"
        if "user" in fields:
            context["user"] = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
        if "location" in fields:
            location = self._get_ip_location()
            if location:
                context["location"] = location

        return context

    def _get_ip_location(self) -> str | None:
        """Get location from IP geolocation (cached)."""
        if AgentRuntime._cached_location is not None:
            return AgentRuntime._cached_location.get("location")

        try:
            import urllib.request

            with urllib.request.urlopen("http://ip-api.com/json/?fields=city,regionName,country", timeout=2) as response:
                data = json.loads(response.read().decode())
                if data.get("city"):
                    location = f"{data.get('city', '')}, {data.get('regionName', '')}, {data.get('country', '')}"
                    AgentRuntime._cached_location = {"location": location}
                    return location
        except Exception:
            AgentRuntime._cached_location = {"location": None}

        return None

    def _format_runtime_context(self, context: dict[str, Any]) -> str:
        """Format runtime context as a single line for system prompt."""
        parts = []
        if "timestamp" in context:
            parts.append(f"Current time: {context['timestamp']}")
        if "timezone" in context:
            parts.append(f"Timezone: {context['timezone']}")
        if "location" in context:
            parts.append(f"Location: {context['location']}")
        if "user" in context:
            parts.append(f"User: {context['user']}")
        return f"[CONTEXT] {' | '.join(parts)}" if parts else ""

    def _build_native_tools_if_supported(self, agent) -> None:
        """Build native tool schemas if the LLM provider supports native tool calling."""
        llm = self._resolve_llm()
        if not hasattr(llm, "provider"):
            return

        provider_supports = getattr(llm.provider, "supports_native_tools", False)
        if not provider_supports:
            return

        if self._use_native_tools is False:
            return

        # Import here to avoid circular imports
        from dana.core.agent.components.tool_schema import generate_tool_schemas

        self._native_tools = generate_tool_schemas(
            agents=getattr(agent, "_agents", []),
            resources=getattr(agent, "_resources", []),
            workflows=getattr(agent, "_workflows", []),
        )

    def _build_system_prompt(self, agent) -> str:
        """Build the system prompt using the template and hooks."""
        identity = self.get_identity(agent)
        template = self.get_system_prompt_template(native_tools=bool(self._native_tools))

        values = {"identity": identity}

        # Add available tools for JSON mode
        if not self._native_tools:
            values["available_tools_prompt"] = self._build_available_tools_prompt(agent)

        return self._render_template(template, values).strip()

    def _render_template(self, template: str, values: dict[str, str]) -> str:
        rendered = template
        for key, value in values.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", value or "")
        return rendered

    def _build_available_tools_prompt(self, agent) -> str:
        prompts: list[str] = []
        for component in getattr(agent, "_agents", []):
            prompts.extend(self._component_tool_prompts(component))
        for component in getattr(agent, "_resources", []):
            prompts.extend(self._component_tool_prompts(component))
        for component in getattr(agent, "_workflows", []):
            prompts.extend(self._component_tool_prompts(component))
        return ",\n    ".join([prompt for prompt in prompts if prompt])

    def _component_tool_prompts(self, component) -> list[str]:
        tool_methods = Misc.extract_tool_use_methods(component)
        prompts = []
        for _, method in tool_methods:
            signature = Misc.parse_method_signature(method, object_id=getattr(component, "object_id", None))
            prompts.append(self.format_tool_for_prompt(signature))
        return prompts

    def _log_prompt_build(self, agent, system_prompt: str, timeline, messages: list[LLMMessage]) -> None:
        from dana.common.llm.debug_logger import get_debug_logger

        debug_logger = get_debug_logger()
        debug_logger.log_agent_interaction(
            agent_id=agent.object_id,
            agent_type=agent.agent_type,
            interaction_type="build_llm_request",
            content=f"Built {len(messages)} messages for LLM request",
            metadata={
                "message_count": len(messages),
                "system_prompt_length": len(system_prompt),
                "timeline_entries": len(timeline.timeline) if timeline else 0,
            },
        )

    def _extract_json(self, content: str) -> dict[str, Any] | None:
        """Extract JSON object from content."""
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

    def _extract_content_between_xml_tags(self, content: str, tag: str) -> str | None:
        if not content or not tag:
            return None

        escaped_tag = re.escape(tag)
        match = re.search(r"<" + escaped_tag + r">(.*?)</" + escaped_tag + r">", content, re.DOTALL)
        if match:
            return match.group(1).strip()

        match = re.search(r"<" + escaped_tag + r">([^<]*)", content, re.DOTALL)
        if match:
            captured = match.group(1).strip()
            if not captured:
                match = re.search(r"<" + escaped_tag + r">(.*)", content, re.DOTALL)
                if match:
                    return match.group(1).strip()
            return captured

        return None

    def _to_tool_call_dicts(self, llm_tool_calls: list) -> list[dict[str, Any]]:
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

    def _create_tool_success(self, tool_type: str, target: str, result: Any) -> dict[str, Any]:
        return {"type": tool_type, "target": target, "result": result, "success": True}

    def _create_tool_error(self, tool_type: str, target: str, error_message: str) -> dict[str, Any]:
        return {"type": tool_type, "target": target, "result": f"Error: {error_message}", "success": False}

    def _get_available_class_names(self) -> list[str]:
        classes = []
        for agent in self._agent.available_agents:
            classes.append(agent.__class__.__name__)
        for resource in self._agent.available_resources:
            classes.append(resource.__class__.__name__)
        for workflow in self._agent.available_workflows:
            classes.append(workflow.__class__.__name__)
        return classes

    def _find_object_by_id(self, object_id: str) -> dict[str, Any] | None:
        for agent in self._agent.available_agents:
            if (hasattr(agent, "object_id") and agent.object_id == object_id) or (
                hasattr(agent, "agent_type") and agent.agent_type == object_id
            ):
                return {"type": "agent", "object": agent}

        for resource in self._agent.available_resources:
            if (hasattr(resource, "object_id") and resource.object_id == object_id) or (
                hasattr(resource, "resource_id") and resource.resource_id == object_id
            ):
                return {"type": "resource", "object": resource}

        for workflow in self._agent.available_workflows:
            if (hasattr(workflow, "object_id") and workflow.object_id == object_id) or (
                hasattr(workflow, "workflow_id") and workflow.workflow_id == object_id
            ):
                return {"type": "workflow", "object": workflow}

        self._agent.ensure_registered()
        registry = self._agent._registry
        if registry and object_id in registry._items:
            agent = registry.get(object_id)
            if agent:
                return {"type": "agent", "object": agent}

        return None

    def _find_object_by_class_name(self, class_name: str) -> dict[str, Any] | None:
        for agent in self._agent.available_agents:
            if agent.__class__.__name__ == class_name:
                return {"type": "agent", "object": agent}

        for resource in self._agent.available_resources:
            if resource.__class__.__name__ == class_name:
                return {"type": "resource", "object": resource}

        for workflow in self._agent.available_workflows:
            if workflow.__class__.__name__ == class_name:
                return {"type": "workflow", "object": workflow}

        return None

    def _validate_n_cast_method_arguments(self, method, arguments: dict[str, Any]) -> dict[str, Any]:
        import types
        from typing import Union, get_origin

        try:
            signature = Misc.parse_method_signature(method)
        except Exception:
            return arguments

        for param in signature.parameters:
            if param.type_object and param.name in arguments:
                if param.type_object is Any:
                    continue

                origin = get_origin(param.type_object)
                if origin is None:
                    origin = param.type_object

                is_union_type = hasattr(param.type_object, "__args__") and (origin is Union or origin is types.UnionType)
                if is_union_type:
                    hinted_types = param.type_object.__args__
                else:
                    hinted_types = [origin]

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

    def _parse_function_name(self, function_name: str) -> tuple[str, str] | None:
        """Parse function name into (identifier, method_name)."""
        if ":" in function_name:
            return function_name.split(":", 1)
        if "__" in function_name:
            parts = function_name.rsplit("__", 1)
            if len(parts) == 2:
                return parts[0].replace("_", "-"), parts[1]
        return None

    @observable
    def _execute_single_call(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        function_name = tool_call.get("function", "")
        arguments = tool_call.get("arguments", {})

        parsed = self._parse_function_name(function_name)
        if not parsed:
            return self._create_tool_error("format_error", function_name, "Expected ClassName:methodName or object_id__method format")

        identifier, method_name = parsed

        obj_info = self._find_object_by_id(identifier) or self._find_object_by_class_name(identifier)
        if not obj_info:
            available_classes = self._get_available_class_names()
            return self._create_tool_error(
                "class_not_found",
                identifier,
                "Object not found by object_id or class_name. Available classes: "
                + ", ".join(available_classes[:10])
                + ("..." if len(available_classes) > 10 else ""),
            )

        if hasattr(obj_info["object"], method_name):
            method = getattr(obj_info["object"], method_name)
            arguments = self._validate_n_cast_method_arguments(method, arguments)
            try:
                if obj_info["type"] == "agent":
                    if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
                        session_id = self._agent._event_log._current_session_id
                        if session_id is not None:
                            arguments["session_id"] = session_id
                if asyncio.iscoroutinefunction(method):
                    result = Misc.safe_asyncio_run(method, **arguments)
                else:
                    result = method(**arguments)
                return self._create_tool_success(obj_info["type"], f"{identifier}.{method_name}", result)
            except Exception as exc:
                return self._create_tool_error(
                    "execution_error",
                    f"{identifier}.{method_name}",
                    f"Error executing call {identifier}.{method_name}: {exc}\n{traceback.format_exc()}",
                )

        return self._create_tool_error(
            "method_not_found",
            f"{identifier}.{method_name}",
            f"Method '{method_name}' not found in object '{identifier}'\n{traceback.format_exc()}",
        )

    @observable
    async def _execute_single_call_async(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        function_name = tool_call.get("function", "")
        arguments = tool_call.get("arguments", {})

        parsed = self._parse_function_name(function_name)
        if not parsed:
            return self._create_tool_error("format_error", function_name, "Expected ClassName:methodName or object_id__method format")

        identifier, method_name = parsed

        obj_info = self._find_object_by_id(identifier) or self._find_object_by_class_name(identifier)
        if not obj_info:
            available_classes = self._get_available_class_names()
            return self._create_tool_error(
                "class_not_found",
                identifier,
                "Object not found by object_id or class_name. Available classes: "
                + ", ".join(available_classes[:10])
                + ("..." if len(available_classes) > 10 else ""),
            )

        actual_method_name = method_name
        if obj_info["type"] == "agent" and method_name == "query":
            actual_method_name = "aquery"

        if hasattr(obj_info["object"], actual_method_name):
            method = getattr(obj_info["object"], actual_method_name)
            arguments = self._validate_n_cast_method_arguments(method, arguments)
            try:
                if obj_info["type"] == "agent":
                    if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
                        session_id = self._agent._event_log._current_session_id
                        if session_id is not None:
                            arguments["session_id"] = session_id
                if asyncio.iscoroutinefunction(method):
                    result = await method(**arguments)
                else:
                    result = method(**arguments)
                return self._create_tool_success(obj_info["type"], f"{identifier}.{actual_method_name}", result)
            except Exception as exc:
                return self._create_tool_error(
                    "execution_error",
                    f"{identifier}.{actual_method_name}",
                    f"Error executing call {identifier}.{actual_method_name}: {exc}\n{traceback.format_exc()}",
                )

        return self._create_tool_error(
            "method_not_found",
            f"{identifier}.{actual_method_name}",
            f"Method '{actual_method_name}' not found in object '{identifier}'\n{traceback.format_exc()}",
        )
