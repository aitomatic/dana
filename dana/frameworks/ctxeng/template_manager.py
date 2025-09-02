"""
Template Manager for the Context Engineering Framework.
"""

import logging

from .assemblers import BaseTemplate

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages prompt templates for different use cases and formats."""

    def __init__(self):
        self._templates = {}
        self._load_templates()

    def _load_templates(self):
        """Load all available templates."""
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
        """Get template by name and format."""
        try:
            return self._templates[format_type][template_name]
        except KeyError:
            logger.warning(f"Template {template_name} not found for format {format_type}, using general")
            return self._templates[format_type]["general"]

    def list_templates(self, format_type: str = None) -> list[str]:
        """List available templates."""
        if format_type:
            return list(self._templates[format_type].keys())
        else:
            return list(self._templates["xml"].keys())  # Default to XML


# Import template implementations
from .templates.text.analysis import TextAnalysisTemplate
from .templates.text.conversation import TextConversationTemplate
from .templates.text.general import TextGeneralTemplate
from .templates.text.problem_solving import TextProblemSolvingTemplate
from .templates.xml.analysis import XMLAnalysisTemplate
from .templates.xml.conversation import XMLConversationTemplate
from .templates.xml.general import XMLGeneralTemplate
from .templates.xml.problem_solving import XMLProblemSolvingTemplate
