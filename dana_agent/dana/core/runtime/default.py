from __future__ import annotations

import asyncio
from datetime import datetime
import inspect
import os
import re
import traceback
from typing import Any

import structlog

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage, LLMResponse
from dana.common.observable import observable
from dana.common.protocols.types import LearningPhase
from dana.common.utils.misc import Misc
from dana.core.agent.components.tool_schema import generate_tool_schemas
from dana.core.context import ContextBuilder
from dana.core.runtime import AgentRuntime, ParsedResponse


logger = structlog.get_logger()


TEMPLATE_SYSTEM_PROMPT = """
{{identity}}

You have tools available. Use them when needed to accomplish tasks.

## Output Format

EVERY response must be valid JSON with this structure:

```json
{"done": false, "reasoning": "Brief explanation of your thought process", "response": null, "tool_calls": [{"name": "tool_name", "parameters": {...}}]}
```
OR
```json
{"done": true, "reasoning": "Brief explanation of your thought process", "response": "Your final answer here", "tool_calls": []}
```

Rules:
- `done: false` = you need to call tools, `tool_calls` must not be empty
- `done: true` = you have the answer, `response` must not be empty
- `reasoning` = brief internal thought process (1-2 sentences)
- Output ONLY valid JSON, no other text

## Guidelines

- Be PERSISTENT: try 2-3 different approaches before giving up
- Be THOROUGH: gather complete information before responding
- NEVER mention tool names to users

## Available Tools

{{available_tools_prompt}}
"""


class DefaultRuntime(AgentRuntime):
    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0,
        max_tokens: int | None = None,
        llm: LLM | None = None,
        provider: str = "anthropic",
    ):
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._llm = llm
        self._provider = provider
        self._agent = None
        self._native_tools = None
        self._last_llm_response: LLMResponse | None = None

    @property
    def llm(self) -> LLM | None:
        return self._llm

    def set_llm(self, llm: LLM) -> None:
        self._llm = llm

    def public_description(self, agent) -> str:
        return inspect.getdoc(agent.__class__) or f"{agent.agent_type} agent."

    def private_identity(self, agent) -> str:
        return f"I am a {agent.agent_type} agent with ID {agent.object_id}."

    def system_prompt(self, agent) -> str:
        return self._build_system_prompt(agent)

    @observable
    def build_prompt(self, agent, timeline, learned_context: str | None = None) -> list[LLMMessage]:
        self._agent = agent
        messages = []

        # Inject ephemeral runtime context (time, user, timezone)
        if timeline:
            timeline.set_context(self._get_runtime_context())

        system_prompt = self._build_system_prompt(agent)
        messages.append(LLMMessage(role="system", content=system_prompt))

        if timeline:
            timeline_messages = timeline.to_llm_messages(separate_latest_user=True)
            if timeline_messages and timeline_messages[-1].role == "user":
                context_messages = timeline_messages[:-1]
                latest_user_message = timeline_messages[-1]

                task = latest_user_message.content

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

                if context_messages or context.text:
                    timeline_lines = ["<CONTEXT>"]
                    if context_messages:
                        timeline_lines.append("<TIMELINE>")
                        for msg in context_messages:
                            timeline_lines.append(f"<ENTRY>{msg.content}</ENTRY>")
                        timeline_lines.append("</TIMELINE>")
                    if context.text:
                        timeline_lines.append(context.text)
                    timeline_lines.append("</CONTEXT>")
                    messages.append(LLMMessage(role="assistant", content="\n".join(timeline_lines)))

                user_parts = [latest_user_message.content]
                if learned_context:
                    user_parts.append(f"\n{learned_context}")

                learner = getattr(agent, "_learner", None)
                if learner is not None:
                    related_acquisitive = learner.query_learnings(task, LearningPhase.ACQUISITIVE)
                    if related_acquisitive:
                        user_parts.append(f"\nLearning from the past: {related_acquisitive}")
                    related_retentive = learner.query_learnings(task, LearningPhase.RETENTIVE)
                    if related_retentive:
                        user_parts.append(f"\nRelevant memories from past sessions: {related_retentive}")

                messages.append(LLMMessage(role="user", content="\n".join(user_parts)))
            else:
                messages.extend(timeline_messages)

        self._build_native_tools_if_supported(agent)
        self._log_prompt_build(agent, system_prompt, timeline, messages)

        return messages

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
        )
        self._last_llm_response = response
        return response.content

    @observable
    def parse_response(self, raw: str) -> ParsedResponse:
        if raw is None:
            return ParsedResponse(done=None, reasoning=None, response=None, tool_calls=[])

        content = raw.strip()
        done = None
        response_text = None
        tool_calls: list[dict[str, Any]] = []

        # Check for native tool calls from the LLM response (API-level)
        has_native_tool_calls = False
        if self._last_llm_response and self._last_llm_response.tool_calls:
            tool_calls.extend(self._to_tool_call_dicts(self._last_llm_response.tool_calls))
            has_native_tool_calls = True
            done = False  # Native tool calls mean we're not done

        # Try to parse JSON from content (even with native tools - may contain reasoning)
        reasoning = None
        if content:
            parsed_json = self._extract_json(content)
            if parsed_json:
                reasoning = parsed_json.get("reasoning")
                # Only extract done/response/tool_calls from JSON if no native tool calls
                if not has_native_tool_calls:
                    done = parsed_json.get("done")
                    response_text = parsed_json.get("response")
                    json_tool_calls = parsed_json.get("tool_calls", [])
                    if json_tool_calls:
                        for tc in json_tool_calls:
                            name = tc.get("name", "")
                            params = tc.get("parameters", {})
                            tool_calls.append({"function": name, "arguments": params})
            elif has_native_tool_calls:
                # With native tools, plain text content is the LLM's reasoning/explanation
                reasoning = content

        # If using native tools and LLM returns plain text (no JSON, no tool calls), treat as final response
        if self._native_tools and done is None and not tool_calls and content:
            response_text = content
            done = True

        return ParsedResponse(
            done=done,
            reasoning=reasoning,
            response=response_text if response_text else None,
            tool_calls=tool_calls,
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

    def _resolve_llm(self) -> LLM:
        if self._llm is not None:
            return self._llm
        if self._agent is not None and getattr(self._agent, "_llm_client", None) is not None:
            return self._agent.llm_client
        self._llm = LLM(provider=self._provider, model=self._model)
        if self._agent is not None:
            self._agent.llm_client = self._llm
        return self._llm

    # Cache for IP geolocation (doesn't change during session)
    _cached_location: dict[str, str] | None = None

    def _get_runtime_context(self) -> dict[str, Any]:
        """Get runtime context info for the current query.

        Returns:
            Dictionary with timestamp, timezone, user, and location info.
        """
        now = datetime.now().astimezone()
        context = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": now.tzname() or "UTC",
            "user": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        }

        # Add location from IP geolocation (cached)
        location = self._get_ip_location()
        if location:
            context["location"] = location

        return context

    def _get_ip_location(self) -> str | None:
        """Get location from IP geolocation (cached).

        Uses ip-api.com which is free and doesn't require an API key.
        Results are cached for the session since location doesn't change.

        Returns:
            Location string like "San Francisco, California, US" or None on failure.
        """
        if DefaultRuntime._cached_location is not None:
            return DefaultRuntime._cached_location.get("location")

        try:
            import json
            import urllib.request

            with urllib.request.urlopen("http://ip-api.com/json/?fields=city,regionName,country", timeout=2) as response:
                data = json.loads(response.read().decode())
                if data.get("city"):
                    location = f"{data.get('city', '')}, {data.get('regionName', '')}, {data.get('country', '')}"
                    DefaultRuntime._cached_location = {"location": location}
                    return location
        except Exception:
            # Fail silently - location is optional
            DefaultRuntime._cached_location = {"location": None}

        return None

    def _build_native_tools_if_supported(self, agent) -> None:
        """Build native tool schemas if the LLM provider supports native tool calling."""
        llm = self._resolve_llm()
        if not hasattr(llm, "provider"):
            return
        if not getattr(llm.provider, "supports_native_tools", False):
            return
        self._native_tools = generate_tool_schemas(
            agents=getattr(agent, "_agents", []),
            resources=getattr(agent, "_resources", []),
            workflows=getattr(agent, "_workflows", []),
        )

    def _build_system_prompt(self, agent) -> str:
        identity = inspect.getdoc(agent.__class__) or f"{agent.agent_type} agent."
        available_tools_prompt = self._build_available_tools_prompt(agent)
        return self._render_template(
            TEMPLATE_SYSTEM_PROMPT,
            {
                "identity": identity,
                "available_tools_prompt": available_tools_prompt,
            },
        ).strip()

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
        return "\n".join([prompt for prompt in prompts if prompt]).strip()

    def _component_tool_prompts(self, component) -> list[str]:
        tool_methods = Misc.extract_tool_use_methods(component)
        prompts = []
        for _, method in tool_methods:
            signature = Misc.parse_method_signature(method, object_id=getattr(component, "object_id", None))
            prompts.append(self._format_signature(signature))
        return prompts

    def _format_signature(self, signature) -> str:
        import json

        identifier = signature.object_id or signature.class_name or "Unknown"
        tool_name = f"{identifier}:{signature.name}"

        # Build compact parameter list
        param_parts = []
        for p in signature.parameters:
            req = " (required)" if not p.has_default else ""
            param_parts.append(f"  - {p.name}{req}: {p.description}")
        params_str = "\n".join(param_parts) if param_parts else "  (none)"

        # Build JSON usage example matching output format
        params_example = {}
        for p in signature.parameters:
            params_example[p.name] = p.example if p.example else f"<{p.name}>"
        usage = json.dumps({"name": tool_name, "parameters": params_example})

        return f"**{tool_name}**: {signature.description}\n{params_str}\nExample: {usage}"

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

    def _extract_done_flag(self, content: str) -> bool | None:
        done_text = self._extract_content_between_xml_tags(content, "done")
        if done_text is None:
            return None
        normalized = done_text.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
        return None

    def _extract_tool_calls_from_function_call(self, function_call_xml: str) -> list[dict[str, Any]]:
        if not function_call_xml or not function_call_xml.strip():
            return []

        tool_calls: list[dict[str, Any]] = []
        invoke_pattern = r'<invoke\s+name=["\']([^"\']+)["\']\s*>(.*?)</invoke>'
        for match in re.finditer(invoke_pattern, function_call_xml, re.DOTALL):
            function_name = match.group(1).strip()
            params_content = match.group(2)
            arguments: dict[str, Any] = {}

            param_pattern = r'<parameter\s+name=["\']([^"\']+)["\'][^>]*>(.*?)</parameter>'
            for param_match in re.finditer(param_pattern, params_content, re.DOTALL):
                param_name = param_match.group(1)
                param_value = param_match.group(2).strip()
                arguments[param_name] = param_value

            tool_calls.append({"function": function_name, "arguments": arguments})

        return tool_calls

    def _extract_json(self, content: str) -> dict[str, Any] | None:
        """Extract JSON object from content, handling markdown code blocks."""
        import json as json_module

        if not content:
            return None

        # Try to find JSON in markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            try:
                return json_module.loads(json_match.group(1))
            except json_module.JSONDecodeError:
                pass

        # Try to parse the whole content as JSON
        try:
            return json_module.loads(content)
        except json_module.JSONDecodeError:
            pass

        # Try to find a JSON object anywhere in the content
        json_match = re.search(r'\{[^{}]*"done"[^{}]*\}', content, re.DOTALL)
        if json_match:
            try:
                return json_module.loads(json_match.group(0))
            except json_module.JSONDecodeError:
                pass

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
        import json

        tool_call_dicts = []
        for llm_tool_call in llm_tool_calls:
            try:
                tool_call_id = getattr(llm_tool_call, "id", None)
                function_name = llm_tool_call.function.name
                arguments = llm_tool_call.function.arguments
                # Parse arguments if it's a JSON string (native OpenAI format)
                if isinstance(arguments, str):
                    arguments = json.loads(arguments) if arguments else {}
                call_dict = {"function": function_name, "arguments": arguments}
                if tool_call_id:
                    call_dict["tool_call_id"] = tool_call_id
                tool_call_dicts.append(call_dict)
            except Exception:
                continue
        return tool_call_dicts

    def _create_tool_success(self, tool_type: str, target: str, result: str) -> dict[str, Any]:
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
        import json
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

    def _parse_function_name(self, function_name: str) -> tuple[str, str] | None:
        """Parse function name into (identifier, method_name).

        Supports two formats:
        - XML format: 'ClassName:methodName' (colon separator)
        - Native OpenAI format: 'object_id__method_name' (double underscore separator)
        """
        if ":" in function_name:
            return function_name.split(":", 1)
        if "__" in function_name:
            # Native OpenAI format: object_id__method_name
            # Split on last __ to handle object_ids that might contain underscores
            parts = function_name.rsplit("__", 1)
            if len(parts) == 2:
                return parts[0].replace("_", "-"), parts[1]  # Restore hyphens in object_id
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
