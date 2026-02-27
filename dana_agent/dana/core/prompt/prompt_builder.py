"""
PromptBuilder: encapsulates all prompt-construction logic for AgentRuntime.

Implements PromptBuilderProtocol. AgentRuntime creates one instance and
delegates build_prompt (and related methods) to it.

Design:
- Customisation hooks are injected as callables (identity_fn, template_fn, etc.)
  so that subclass overrides (Anthropic/OpenAI) are picked up transparently.
- Stateless w.r.t. the agent — agent/timeline are method params, not stored state.
- runtime_context (dict) is computed by AgentRuntime (which owns the IP cache)
  and passed in at call time, keeping the two caches consolidated.
- native_tools is passed in at call time (owned by AgentRuntime).
- system_prompt_fn: optional override for system prompt generation (codec path).
- context_position: "prepend" (JSON path) or "append" (codec path).
- skip_retrieved_context: True for codec runtimes (they handle context differently).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from dana.common.llm.types import LLMMessage
from dana.common.protocols.types import LearningPhase
from dana.common.utils.misc import Misc
from dana.core.context import ContextBuilder
from dana.core.prompt.prompt_builder_helpers import (
    TaggedQueryable,
    format_runtime_context,
    log_prompt_build,
    render_template,
)


if TYPE_CHECKING:
    from dana.core.agent.timeline import Timeline


class PromptBuilder:
    """
    Builds the list of LLMMessages for a given agent + timeline.

    All customisation hooks are injected as callables so subclass overrides
    on AgentRuntime are automatically picked up when the runtime passes
    ``self.get_identity``, ``self.get_system_prompt_template``, etc.

    Codec path customisation:
    - system_prompt_fn: replaces _build_system_prompt() entirely (e.g. LocalPromptAPI.system_prompt)
    - context_position: "prepend" places context_line before system_prompt (JSON path default);
      "append" places it after (codec path behavior)
    - skip_retrieved_context: True skips _build_retrieved_context() injection (codec handles it)
    """

    def __init__(
        self,
        *,
        identity_fn: Callable[[Any], str],
        template_fn: Callable[[bool], str],
        format_tool_fn: Callable[[Any], str],
        system_prompt_fn: Callable[[], str] | None = None,
        context_position: str = "prepend",
        skip_retrieved_context: bool = False,
    ) -> None:
        self._identity_fn = identity_fn
        self._template_fn = template_fn
        self._format_tool_fn = format_tool_fn
        self._system_prompt_fn = system_prompt_fn
        self._context_position = context_position
        self._skip_retrieved_context = skip_retrieved_context

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def build_prompt(
        self,
        agent: Any,
        timeline: Timeline,
        learned_context: str | None = None,
        *,
        native_tools: Any,
        runtime_context: dict[str, Any],
    ) -> list[LLMMessage]:
        """Build LLM messages from agent + timeline.

        Args:
            agent: The STARAgent instance.
            timeline: Current conversation timeline.
            learned_context: Optional pre-retrieved learned context string.
            native_tools: The runtime's current native tools list (may be None).
            runtime_context: Pre-computed context dict from AgentRuntime._get_runtime_context().
        """
        messages: list[LLMMessage] = []

        # Inject ephemeral runtime context into timeline
        if timeline:
            timeline.set_context(runtime_context)

        # Build system prompt — use override fn if provided (codec path)
        if self._system_prompt_fn is not None:
            system_prompt = self._system_prompt_fn()
        else:
            system_prompt = self._build_system_prompt(agent, native_tools)

        # Position context_line relative to system_prompt based on path
        context_line = format_runtime_context(runtime_context)
        if context_line:
            if self._context_position == "append":
                full_system_prompt = f"{system_prompt}\n\n{context_line}"
            else:
                # Default: prepend (JSON runtime path)
                full_system_prompt = f"{context_line}\n\n{system_prompt}"
        else:
            full_system_prompt = system_prompt

        messages.append(
            LLMMessage(
                role="system",
                content=full_system_prompt,
                cache_control={"type": "ephemeral"},
            )
        )

        if timeline:
            if not self._skip_retrieved_context:
                task = self._get_latest_user_task(timeline)

                # Inject retrieved context (learnings, ltmemory, resources)
                context_text = self._build_retrieved_context(agent, timeline, task, learned_context)
                if context_text:
                    messages.append(LLMMessage(role="user", content=f"<CONTEXT>\n{context_text}\n</CONTEXT>"))

            # Append timeline messages
            messages.extend(timeline.to_llm_messages())

            # Inject system reminders
            self._evaluate_reminders(agent, messages)

        log_prompt_build(agent, system_prompt, timeline, messages)
        return messages

    # ------------------------------------------------------------------
    # System prompt assembly
    # ------------------------------------------------------------------

    def _build_system_prompt(self, agent: Any, native_tools: Any) -> str:
        identity = self._identity_fn(agent)
        template = self._template_fn(bool(native_tools))

        values: dict[str, str] = {"identity": identity}
        values["resource_context"] = self._build_resource_context(agent)

        if not native_tools:
            values["available_tools_prompt"] = self._build_available_tools_prompt(agent)

        return render_template(template, values).strip()

    def _build_resource_context(self, agent: Any) -> str:
        """Concatenate get_prompt_context() from all resources."""
        contexts = []
        for resource in getattr(agent, "_resources", []):
            if hasattr(resource, "get_prompt_context"):
                ctx = resource.get_prompt_context()
                if ctx:
                    contexts.append(ctx)
        return "\n\n".join(contexts)

    def _build_available_tools_prompt(self, agent: Any) -> str:
        prompts: list[str] = []
        for component in getattr(agent, "_agents", []):
            prompts.extend(self._component_tool_prompts(component))
        for component in getattr(agent, "_resources", []):
            prompts.extend(self._component_tool_prompts(component))
        for component in getattr(agent, "_workflows", []):
            prompts.extend(self._component_tool_prompts(component))
        return ",\n    ".join([p for p in prompts if p])

    def _component_tool_prompts(self, component: Any) -> list[str]:
        tool_methods = Misc.extract_tool_use_methods(component)
        prompts = []
        for _, method in tool_methods:
            signature = Misc.parse_method_signature(method, object_id=getattr(component, "object_id", None))
            prompts.append(self._format_tool_fn(signature))
        return prompts

    # ------------------------------------------------------------------
    # Retrieved context (learnings, ltmemory, resource queries)
    # ------------------------------------------------------------------

    def _build_retrieved_context(
        self,
        agent: Any,
        timeline: Timeline,
        task: str,
        learned_context: str | None,
    ) -> str:
        if not task:
            return ""

        context_parts: list[str] = []

        if learned_context:
            context_parts.append(learned_context)

        learner = getattr(agent, "_learner", None)
        if learner is not None:
            related_acquisitive = learner.query_learnings(task, LearningPhase.ACQUISITIVE)
            if related_acquisitive:
                context_parts.append(f"Learning from the past: {related_acquisitive}")
            related_retentive = learner.query_learnings(task, LearningPhase.RETENTIVE)
            if related_retentive:
                context_parts.append(f"Relevant memories from past sessions: {related_retentive}")

        ctx = ContextBuilder(token_budget=getattr(timeline, "max_context_tokens", 100000))
        ltmemory = getattr(agent, "_ltmemory", None)
        if ltmemory is not None:
            ctx.add_source("ltmemory", TaggedQueryable(ltmemory, "LTMEMORY"))

        for resource in getattr(agent, "_resources", []):
            if hasattr(resource, "query") and hasattr(resource, "resource_id"):
                ctx.add_source(resource.resource_id, TaggedQueryable(resource, resource.resource_id.upper()))

        context = ctx.build(task=task)
        if context.text:
            context_parts.append(context.text)

        return "\n\n".join(context_parts) if context_parts else ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_latest_user_task(self, timeline: Timeline) -> str:
        from dana.core.agent.timeline import TimelineEntryType

        for entry in reversed(timeline.timeline):
            if entry.entry_type == TimelineEntryType.USER_MESSAGE:
                return entry.content
        return ""

    def _evaluate_reminders(self, agent: Any, messages: list[LLMMessage]) -> None:
        if not hasattr(agent, "_reminder_manager") or agent._reminder_manager is None:
            return
        agent._reminder_manager.evaluate_all(agent, messages)
