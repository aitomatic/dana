"""
XML Conversation Template for the Context Engineering Framework.
"""

from typing import Any

from ...assemblers import XMLTemplate


class XMLConversationTemplate(XMLTemplate):
    """Template for conversational prompts."""

    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble conversation prompt in XML format."""
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
        return ["query"]

    def get_optional_context(self) -> list[str]:
        return ["conversation_history", "recent_events"]
