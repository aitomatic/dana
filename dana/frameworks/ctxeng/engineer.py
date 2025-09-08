"""
Context Engineer - Core logic for context assembly and optimization.
"""

import logging
from typing import Any

from .context_data import ContextData
from .templates.manager import TemplateManager

logger = logging.getLogger(__name__)


class ContextEngineer:
    """Core engineer responsible for context assembly and optimization.

    This class encapsulates the actual work of context engineering:
    - Template selection and detection
    - Context collection from resources
    - Relevance scoring and filtering
    - Token optimization
    - Final prompt assembly
    """

    def __init__(self, format_type: str = "xml", max_tokens: int = 1500, relevance_threshold: float = 0.7):
        """
        Initialize the context engineer.

        Args:
            format_type: Output format ("xml" or "text")
            max_tokens: Maximum tokens for context assembly
            relevance_threshold: Minimum relevance score for context pieces
        """
        self.format_type = format_type
        self.max_tokens = max_tokens
        self.relevance_threshold = relevance_threshold
        self._template_manager = TemplateManager()

    def engineer_context(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        template: str | None = None,
        **options,
    ) -> str:
        """
        Engineer optimized context for the query.

        Args:
            query: What the user is asking
            context: Optional additional context
            template: Template name (e.g., "problem_solving", "conversation")
            **options: Additional options

        Returns:
            Optimized prompt string (XML or text format)
        """
        # Use provided context or empty dict
        context = context or {}

        # Auto-detect template if not specified
        if not template:
            template = self._detect_template(query, context, options)

        # Apply relevance filtering and token optimization
        optimized_context = self._optimize_context(context, query, template, options)

        # Get template and assemble final prompt
        template_obj = self._template_manager.get_template(template, self.format_type)
        return template_obj.assemble(query, optimized_context, options)

    def engineer_context_structured(
        self,
        context_data: ContextData,
        **options,
    ) -> str:
        """
        Engineer optimized context using structured ContextData.

        Args:
            context_data: Structured context data object
            **options: Additional options

        Returns:
            Optimized prompt string (XML or text format)
        """
        # Convert structured data to dictionary for template processing
        context_dict = context_data.to_dict()

        # Use the structured data's template and query
        query = context_data.query
        template = context_data.template

        # Apply relevance filtering and token optimization
        optimized_context = self._optimize_context(context_dict, query, template, options)

        # Get template and assemble final prompt
        template_obj = self._template_manager.get_template(template, self.format_type)
        return template_obj.assemble(query, optimized_context, options)

    def _detect_template(self, query: str, context: dict[str, Any], options: dict[str, Any]) -> str:
        """Auto-detect appropriate template if not specified."""
        if options.get("use_case"):
            return options["use_case"]

        # Simple keyword-based detection
        query_lower = query.lower()
        if any(word in query_lower for word in ["plan", "solve", "create", "build"]):
            return "problem_solving"
        elif any(word in query_lower for word in ["chat", "talk", "discuss"]):
            return "conversation"
        elif any(word in query_lower for word in ["analyze", "examine", "study"]):
            return "analysis"
        else:
            return "general"

    def _optimize_context(self, context: dict[str, Any], query: str, template: str, options: dict[str, Any]) -> dict[str, Any]:
        """Apply relevance filtering and token optimization to context."""
        # For now, return context as-is
        # TODO: Implement relevance scoring and token optimization
        return context

    def get_available_templates(self, format_type: str | None = None) -> list[str]:
        """Get list of available templates."""
        return self._template_manager.list_templates(format_type)

    def get_template_info(self, template_name: str, format_type: str | None = None) -> dict[str, Any]:
        """Get information about a specific template."""
        format_type = format_type or self.format_type
        template = self._template_manager.get_template(template_name, format_type)
        return {
            "name": template_name,
            "format": format_type,
            "required_context": template.get_required_context(),
            "optional_context": template.get_optional_context(),
        }

    # ===================== Factory Methods =====================

    @classmethod
    def from_agent(cls, agent: Any, **config) -> "ContextEngineer":
        """Create a context engineer for an agent (simplified - no resource discovery)."""
        return cls(**config)
