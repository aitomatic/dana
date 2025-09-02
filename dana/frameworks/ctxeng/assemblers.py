"""
Base template classes for the Context Engineering Framework.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTemplate(ABC):
    """Base class for all prompt templates."""

    @abstractmethod
    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble prompt using this template."""
        pass

    def get_required_context(self) -> list[str]:
        """Get list of required context keys for this template."""
        return []

    def get_optional_context(self) -> list[str]:
        """Get list of optional context keys for this template."""
        return []


class XMLTemplate(BaseTemplate):
    """Base class for XML format templates."""

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters."""
        if not text:
            return ""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

    def _build_xml_element(self, tag: str, content: str, attributes: dict[str, str] = None) -> str:
        """Build XML element with optional attributes."""
        if attributes:
            attrs = " ".join(f'{k}="{self._escape_xml(str(v))}"' for k, v in attributes.items())
            return f"<{tag} {attrs}>{self._escape_xml(content)}</{tag}>"
        else:
            return f"<{tag}>{self._escape_xml(content)}</{tag}>"


class TextTemplate(BaseTemplate):
    """Base class for text format templates."""

    def _format_text_element(self, label: str, content: Any) -> str:
        """Format text element with label."""
        if not content:
            return ""
        return f"{label.upper()}: {content}\n"
