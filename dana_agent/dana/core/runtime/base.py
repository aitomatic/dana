"""
Base runtime class with common logic and customization hooks.

This module provides BaseRuntime, which contains all the shared functionality
for agent runtimes. Subclasses override specific hooks to customize behavior
for different LLM providers.
"""

from __future__ import annotations

from abc import ABC
import inspect
import json
from typing import TYPE_CHECKING, Any

import structlog

from dana.common.llm.llm import LLM
from dana.common.llm.types import LLMMessage, LLMResponse
from dana.common.observable import observable
from dana.common.utils.misc import Misc
from dana.core.llm.llm_caller import LLMCaller
from dana.core.llm.response_parser import JSONResponseParser
from dana.core.prompt.prompt_builder import PromptBuilder
from dana.core.runtime.protocols import ParsedResponse
from dana.core.tool.tool_executor import ToolExecutor


if TYPE_CHECKING:
    from dana.core.agent.timeline import Timeline

logger = structlog.get_logger()


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
        # Registry mapping custom tool names (from @named_tool) to (object, method_name)
        self._tool_name_registry: dict[str, tuple[Any, str]] = {}
        # PromptBuilder is wired with method references so subclass hook overrides
        # (e.g. AnthropicRuntime.get_system_prompt_template) are picked up automatically.
        self._prompt_builder = PromptBuilder(
            identity_fn=self.get_identity,
            template_fn=self.get_system_prompt_template,
            format_tool_fn=self.format_tool_for_prompt,
        )
        # ResponseParser reads _native_tools via lambda so it always sees the current value.
        self._response_parser = JSONResponseParser(
            get_native_tools=lambda: self._native_tools,
        )
        # LLMCaller encapsulates all LLM invocation logic.
        # Lambdas ensure it always sees the current agent and native_tools values.
        self._llm_caller = LLMCaller(
            llm=llm,
            model=model,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            native_tools_getter=lambda: self._native_tools,
            agent_getter=lambda: self._agent,
        )
        # ToolExecutor handles all tool dispatch (sync + async).
        # Lambdas ensure it always sees the current registry and agent.
        self._tool_executor = ToolExecutor(
            tool_name_registry_getter=lambda: self._tool_name_registry,
        )

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def llm(self) -> LLM | None:
        return self._llm

    def set_llm(self, llm: LLM) -> None:
        self._llm = llm
        self._llm_caller.set_llm(llm)

    def validate_done_output(self, done: bool | None, has_tool_calls: bool, has_response: bool) -> str:
        """Validate the output format and return the next action. Delegates to JSONResponseParser."""
        return self._response_parser.validate_done_output(done, has_tool_calls, has_response)

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
        return self._prompt_builder._build_system_prompt(agent, self._native_tools)

    @observable
    def build_prompt(self, agent, timeline: Timeline, learned_context: str | None = None) -> list[LLMMessage]:
        """Build LLM messages from timeline. Delegates to PromptBuilder."""
        self._agent = agent

        # Build native tools first (affects system prompt template choice)
        self._build_native_tools_if_supported(agent)

        # Build tool name registry for @named_tool decorated methods
        self._build_tool_name_registry(agent)

        # Compute runtime context here — AgentRuntime owns the IP cache
        runtime_context = self._get_runtime_context()

        return self._prompt_builder.build_prompt(
            agent,
            timeline,
            learned_context,
            native_tools=self._native_tools,
            runtime_context=runtime_context,
        )

    def call_llm(self, messages: list[LLMMessage]) -> LLMResponse:
        """Sync LLM call. Delegates to LLMCaller (observable fires there)."""
        return self._llm_caller.call_llm(messages)

    async def call_llm_async(self, messages: list[LLMMessage]) -> LLMResponse:
        """Async LLM call. Delegates to LLMCaller (observable fires there)."""
        return await self._llm_caller.call_llm_async(messages)

    @observable
    def parse_response(self, response: LLMResponse) -> ParsedResponse:
        """Parse an LLMResponse into a structured ParsedResponse. Delegates to JSONResponseParser."""
        return self._response_parser.parse_response(response)

    @observable
    def execute_tools(self, agent, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sync batch tool executor. Delegates to ToolExecutor (observable fires here)."""
        self._agent = agent
        return self._tool_executor.execute_tools(agent, tool_calls)

    @observable
    async def execute_tools_async(self, agent, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Async batch tool executor. Delegates to ToolExecutor (observable fires here)."""
        self._agent = agent
        return await self._tool_executor.execute_tools_async(agent, tool_calls)

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
        """Lazy LLM resolution. Delegates to LLMCaller."""
        return self._llm_caller._resolve_llm()

    _cached_location: dict[str, str] | None = None

    def _get_runtime_context(self) -> dict[str, Any]:
        """Get runtime context info for the current query."""
        from datetime import datetime
        import os

        fields = self.get_runtime_context_fields()
        context: dict[str, Any] = {}
        now = datetime.now().astimezone()
        if "timestamp" in fields:
            # Use date-only for prompt caching (format_runtime_context reads "date" key)
            context["date"] = now.strftime("%Y-%m-%d")
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
        """Get location from IP geolocation (class-level cache)."""
        import json as _json

        if AgentRuntime._cached_location is not None:
            return AgentRuntime._cached_location.get("location")
        try:
            import urllib.request

            with urllib.request.urlopen("http://ip-api.com/json/?fields=city,regionName,country", timeout=2) as resp:
                data = _json.loads(resp.read().decode())
                if data.get("city"):
                    location = f"{data.get('city', '')}, {data.get('regionName', '')}, {data.get('country', '')}"
                    AgentRuntime._cached_location = {"location": location}
                    return location
        except Exception:
            AgentRuntime._cached_location = {"location": None}
        return None

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
        from dana.core.tool.tool_schema import generate_tool_schemas

        self._native_tools = generate_tool_schemas(
            agents=getattr(agent, "_agents", []),
            resources=getattr(agent, "_resources", []),
            workflows=getattr(agent, "_workflows", []),
        )

    def _build_tool_name_registry(self, agent) -> None:
        """Build mapping from custom tool names to (object, method_name).

        This registry enables execution of tools decorated with @named_tool
        by mapping their custom names back to the actual objects and methods.
        """
        self._tool_name_registry.clear()

        # Register resources
        for resource in getattr(agent, "_resources", []):
            for method_name, method in Misc.extract_tool_use_methods(resource):
                sig = Misc.parse_method_signature(method, object_id=getattr(resource, "object_id", None))
                if sig.tool_name:
                    self._tool_name_registry[sig.tool_name] = (resource, method_name)

        # Register workflows
        for workflow in getattr(agent, "_workflows", []):
            if hasattr(workflow, "execute"):
                sig = Misc.parse_method_signature(workflow.execute, object_id=getattr(workflow, "object_id", None))
                if sig.tool_name:
                    self._tool_name_registry[sig.tool_name] = (workflow, "execute")

        # Register sub-agents (they expose query method)
        for sub_agent in getattr(agent, "_agents", []):
            if hasattr(sub_agent, "query"):
                sig = Misc.parse_method_signature(sub_agent.query, object_id=getattr(sub_agent, "agent_type", None))
                if sig.tool_name:
                    self._tool_name_registry[sig.tool_name] = (sub_agent, "query")
