"""
XML General Template for the Context Engineering Framework.
"""

from typing import Any

from ...assemblers import XMLTemplate


class XMLGeneralTemplate(XMLTemplate):
    """General template for unspecified use cases."""

    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble general prompt in XML format."""
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
        return ["query"]

    def get_optional_context(self) -> list[str]:
        return []  # Accepts any context
