"""
Template Manager for the Context Engineering Framework.
"""

import logging

from .base import BaseTemplate

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages prompt templates for different use cases and formats.

    This class handles template loading, selection, and fallback logic.
    It provides a centralized way to access templates by name and format type.
    """

    def __init__(self):
        """Initialize the template manager and load all available templates."""
        self._templates = {}
        self._load_templates()

    def _load_templates(self):
        """Load all available templates.

        Currently loads the following templates:

        XML Templates:
        - problem_solving: Rich context for complex problem solving
        - conversation: Optimized for conversational interactions
        - analysis: Data-driven analysis and reporting
        - general: Default template for unspecified use cases

        Text Templates:
        - problem_solving: Text version of problem-solving template
        - conversation: Text version of conversation template
        - analysis: Text version of analysis template
        - general: Text version of general template
        """
        # Load XML templates
        self._templates["xml"] = {
            "problem_solving": XMLProblemSolvingTemplate(),
            "conversation": XMLConversationTemplate(),
            "analysis": XMLAnalysisTemplate(),
            "general": XMLGeneralTemplate(),
        }

        # Load text templates
        self._templates["text"] = {
            "problem_solving": TextProblemSolvingTemplate(),
            "conversation": TextConversationTemplate(),
            "analysis": TextAnalysisTemplate(),
            "general": TextGeneralTemplate(),
        }

    def get_template(self, template_name: str, format_type: str) -> BaseTemplate:
        """Get template by name and format.

        Args:
            template_name: Name of the template to retrieve
            format_type: Format type ("xml" or "text")

        Returns:
            Template instance. If the requested template is not found,
            falls back to the "general" template for the specified format.

        Note:
            This method implements fallback logic - if a template is not found,
            it automatically returns the "general" template instead of raising
            an error. This ensures the system always has a working template.
        """
        try:
            return self._templates[format_type][template_name]
        except KeyError:
            logger.warning(f"Template {template_name} not found for format {format_type}, using general")
            return self._templates[format_type]["general"]

    def list_templates(self, format_type: str | None = None) -> list[str]:
        """List available templates.

        Args:
            format_type: Optional format type to filter by ("xml" or "text")

        Returns:
            List of available template names. If format_type is specified,
            returns templates for that format only. Otherwise returns XML
            templates as the default.
        """
        if format_type:
            return list(self._templates[format_type].keys())
        else:
            return list(self._templates["xml"].keys())  # Default to XML


# Import template implementations
from .text.analysis import TextAnalysisTemplate
from .text.conversation import TextConversationTemplate
from .text.general import TextGeneralTemplate
from .text.problem_solving import TextProblemSolvingTemplate
from .xml.analysis import XMLAnalysisTemplate
from .xml.conversation import XMLConversationTemplate
from .xml.general import XMLGeneralTemplate
from .xml.problem_solving import XMLProblemSolvingTemplate
