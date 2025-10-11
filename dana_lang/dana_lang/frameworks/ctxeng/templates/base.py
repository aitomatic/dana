"""
Base template classes for the Context Engineering Framework.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTemplate(ABC):
    """Base class for all prompt templates.

    This abstract base class defines the interface that all prompt templates
    must implement. Templates are responsible for assembling context data
    into structured prompts for LLM interactions.
    """

    @abstractmethod
    def assemble(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Assemble prompt using this template.

        Args:
            query: The user's query or problem statement
            context: Dictionary containing context data relevant to this template
            options: Additional configuration options for the template

        Returns:
            Formatted prompt string according to the template's structure
        """
        pass

    def get_required_context(self) -> list[str]:
        """Get list of required context keys for this template.

        Returns:
            List of context keys that must be present for the template to work.
            If these keys are missing, the template may not function properly.
        """
        return []

    def get_optional_context(self) -> list[str]:
        """Get list of optional context keys for this template.

        Returns:
            List of context keys that enhance the template's output but aren't required.
            These keys provide richer context when available but don't break functionality
            when missing.
        """
        return []


class XMLTemplate(BaseTemplate):
    """Base class for XML format templates.

    This class provides XML-specific functionality for building structured prompts.
    It handles XML escaping and element construction to ensure valid XML output.
    """

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters.

        Args:
            text: Raw text that may contain XML special characters

        Returns:
            Text with XML special characters properly escaped
        """
        if not text:
            return ""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

    def _build_xml_element(self, tag: str, content: str, attributes: dict[str, str] = None) -> str:
        """Build XML element with optional attributes.

        Args:
            tag: The XML tag name
            content: The content inside the XML element
            attributes: Optional dictionary of attribute name-value pairs

        Returns:
            Properly formatted XML element string
        """
        if attributes:
            attrs = " ".join(f'{k}="{self._escape_xml(str(v))}"' for k, v in attributes.items())
            return f"<{tag} {attrs}>{self._escape_xml(content)}</{tag}>"
        else:
            return f"<{tag}>{self._escape_xml(content)}</{tag}>"


class TextTemplate(BaseTemplate):
    """Base class for text format templates.

    This class provides text-specific functionality for building human-readable prompts.
    It handles text formatting and element construction for plain text output.
    """

    def _format_text_element(self, label: str, content: Any) -> str:
        """Format text element with label.

        Args:
            label: The label for this content element
            content: The content to format

        Returns:
            Formatted text string with label and content
        """
        if not content:
            return ""
        return f"{label.upper()}: {content}\n"
