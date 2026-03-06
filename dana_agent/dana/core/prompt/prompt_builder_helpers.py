"""
Stateless utility functions for prompt building.

These helpers are pure functions (no external I/O) used by PromptBuilder
and as backward-compat shims on AgentRuntime.
"""

from __future__ import annotations

from typing import Any

import structlog


logger = structlog.get_logger()


class TaggedQueryable:
    """Wraps a queryable source and tags its output with XML-style tags.

    Used by PromptBuilder._build_retrieved_context() to tag ltmemory and
    resource query results for inclusion in the context block.
    """

    def __init__(self, source: Any, tag: str) -> None:
        self._source = source
        self._tag = tag

    def query(self, question: str) -> str:
        result = self._source.query(question)
        return f"<{self._tag}>\n{result}\n</{self._tag}>"


def format_runtime_context(context: dict[str, Any]) -> str:
    """Format runtime context dict as a single [CONTEXT] line for system prompt."""
    parts = []
    # NOTE: Skip timestamp for prompt caching, use date instead
    if "date" in context:
        parts.append(f"Current date: {context['date']}")
    if "timezone" in context:
        parts.append(f"Timezone: {context['timezone']}")
    if "location" in context:
        parts.append(f"Location: {context['location']}")
    if "user" in context:
        parts.append(f"User: {context['user']}")
    return f"[CONTEXT] {' | '.join(parts)}" if parts else ""


def render_template(template: str, values: dict[str, str]) -> str:
    """Replace {{key}} placeholders in template with values."""
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value or "")
    return rendered


def log_prompt_build(agent: Any, system_prompt: str, timeline: Any, messages: list) -> None:
    """Log prompt build metadata via the debug logger."""
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
