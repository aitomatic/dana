"""
Text Conversation Template for the Context Engineering Framework.
"""

from typing import Any

from ..base import TextTemplate


class TextConversationTemplate(TextTemplate):
    """Template for conversational prompts in text format."""

    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble conversation prompt in text format."""
        text_parts = []

        # Current message
        text_parts.append(f"MESSAGE: {query}\n")

        # Conversation history
        if context.get("conversation_history"):
            text_parts.append("CONVERSATION HISTORY:\n")
            text_parts.append(f"{context['conversation_history']}\n")

        # Recent events
        if context.get("recent_events"):
            text_parts.append("RECENT EVENTS:\n")
            for event in context["recent_events"]:
                text_parts.append(f"  - {event}\n")

        return "".join(text_parts)

    def get_required_context(self) -> list[str]:
        return ["query"]

    def get_optional_context(self) -> list[str]:
        return ["conversation_history", "recent_events"]
