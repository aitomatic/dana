"""
XML Analysis Template for the Context Engineering Framework.
"""

from typing import Any

from ..base import XMLTemplate


class XMLAnalysisTemplate(XMLTemplate):
    """Template for analysis prompts.

    This template is optimized for data analysis, research, and examination tasks.
    It focuses on data context and analysis parameters to provide rich analytical context.
    """

    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble analysis prompt in XML format.

        Args:
            query: The analysis query or research question
            context: Dictionary containing analysis-specific context data
            options: Additional configuration options (unused in analysis template)

        Context Dictionary Expected Keys:
            query: The analysis question (required)
            data_context: Description of the data being analyzed (optional)
            analysis_params: Dictionary of analysis parameters (optional)

        Context Usage:
            - data_context: Provides information about the dataset, source, format, etc.
            - analysis_params: Includes parameters like time range, filters, aggregation methods, etc.

        Returns:
            XML-formatted prompt string optimized for analytical tasks
        """
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
        """Get list of required context keys for this template.

        Returns:
            List of context keys that must be present for the template to work
        """
        return ["query"]

    def get_optional_context(self) -> list[str]:
        """Get list of optional context keys for this template.

        Returns:
            List of context keys that enhance the analysis but aren't required
        """
        return ["data_context", "analysis_params"]
