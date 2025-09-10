"""
XML Conversation Template for the Context Engineering Framework.
"""

from typing import Any

from ..base import XMLTemplate


class XMLConversationTemplate(XMLTemplate):
    """Template for conversational prompts.

    This template is optimized for ongoing conversations and chat interactions.
    It focuses on conversation history and recent events to maintain context.
    """

    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble conversation prompt in XML format.

        Args:
            query: The current user message or query
            context: Dictionary containing conversation-specific context data
            options: Additional configuration options (unused in conversation template)

        Context Dictionary Expected Keys:
            query: The current message (required)
            conversation_history: Summary of previous conversation turns (optional)
            recent_events: List of recent events or actions (optional)

        Context Usage:
            - conversation_history: Provides continuity and context for ongoing discussions
            - recent_events: Includes recent actions, decisions, or important moments

        Returns:
            XML-formatted prompt string optimized for conversational interactions
        """
        xml_parts = ["<conversation>"]

        # Current message
        xml_parts.append(self._build_xml_element("message", query))

        # Conversation history
        if context.get("conversation_history"):
            xml_parts.append("<history>")
            xml_parts.append(self._build_xml_element("summary", context["conversation_history"]))
            xml_parts.append("</history>")

        # Recent events
        if context.get("recent_events"):
            xml_parts.append("<recent_events>")
            for event in context["recent_events"]:
                xml_parts.append(self._build_xml_element("event", event))
            xml_parts.append("</recent_events>")

        xml_parts.append("</conversation>")

        return "".join(xml_parts)

    def get_required_context(self) -> list[str]:
        """Get list of required context keys for this template.

        Returns:
            List of context keys that must be present for the template to work
        """
        return ["query"]

    def get_optional_context(self) -> list[str]:
        """Get list of optional context keys for this template.

        Returns:
            List of context keys that enhance the conversation but aren't required
        """
        return ["conversation_history", "recent_events"]
