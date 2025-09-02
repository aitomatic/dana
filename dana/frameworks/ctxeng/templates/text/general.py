"""
Text General Template for the Context Engineering Framework.
"""

from typing import Any

from ...assemblers import TextTemplate


class TextGeneralTemplate(TextTemplate):
    """General template for unspecified use cases in text format."""

    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble general prompt in text format."""
        text_parts = []

        # Query
        text_parts.append(f"QUERY: {query}\n")

        # Any available context
        for key, value in context.items():
            if key != "query" and value:
                text_parts.append(f"{key.upper()}: {value}\n")

        return "".join(text_parts)

    def get_required_context(self) -> list[str]:
        return ["query"]

    def get_optional_context(self) -> list[str]:
        return []  # Accepts any context
