"""
XML General Template for the Context Engineering Framework.
"""

from typing import Any

from ..base import XMLTemplate


class XMLGeneralTemplate(XMLTemplate):
    """General template for unspecified use cases.

    This template accepts any context keys and formats them generically.
    It's designed as a fallback when no specific template is available.
    """

    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble general prompt in XML format.

        Args:
            query: The user's query or problem statement
            context: Dictionary containing any available context data
            options: Additional configuration options (unused in general template)

        Context Dictionary Expected Keys:
            query: The main query/problem (required)
            Any other keys: Will be included as-is if they have values

        Returns:
            XML-formatted prompt string with generic structure
        """
        xml_parts = ["<context>"]

        # Query
        xml_parts.append(self._build_xml_element("query", query))

        # Any available context
        for key, value in context.items():
            if key != "query" and value:
                xml_parts.append(self._build_xml_element(key, str(value)))

        xml_parts.append("</context>")

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
            Empty list - this template accepts any context keys
        """
        return []  # Accepts any context
