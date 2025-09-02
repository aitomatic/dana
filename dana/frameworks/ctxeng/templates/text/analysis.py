"""
Text Analysis Template for the Context Engineering Framework.
"""

from typing import Any

from ...assemblers import TextTemplate


class TextAnalysisTemplate(TextTemplate):
    """Template for analysis prompts in text format."""

    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble analysis prompt in text format."""
        text_parts = []

        # Query
        text_parts.append(f"ANALYSIS REQUEST: {query}\n")

        # Data context
        if context.get("data_context"):
            text_parts.append(f"DATA CONTEXT: {context['data_context']}\n")

        # Analysis parameters
        if context.get("analysis_params"):
            text_parts.append("ANALYSIS PARAMETERS:\n")
            for key, value in context["analysis_params"].items():
                text_parts.append(f"  - {key}: {value}\n")

        return "".join(text_parts)

    def get_required_context(self) -> list[str]:
        return ["query"]

    def get_optional_context(self) -> list[str]:
        return ["data_context", "analysis_params"]
