"""
XML Analysis Template for the Context Engineering Framework.
"""

from typing import Any

from ...assemblers import XMLTemplate


class XMLAnalysisTemplate(XMLTemplate):
    """Template for analysis prompts."""

    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble analysis prompt in XML format."""
        xml_parts = ["<analysis>"]

        # Query
        xml_parts.append(self._build_xml_element("query", query))

        # Data context
        if context.get("data_context"):
            xml_parts.append("<data_context>")
            xml_parts.append(self._build_xml_element("description", context["data_context"]))
            xml_parts.append("</data_context>")

        # Analysis parameters
        if context.get("analysis_params"):
            xml_parts.append("<analysis_params>")
            for key, value in context["analysis_params"].items():
                xml_parts.append(self._build_xml_element("param", str(value), {"name": key}))
            xml_parts.append("</analysis_params>")

        xml_parts.append("</analysis>")

        return "".join(xml_parts)

    def get_required_context(self) -> list[str]:
        return ["query"]

    def get_optional_context(self) -> list[str]:
        return ["data_context", "analysis_params"]
