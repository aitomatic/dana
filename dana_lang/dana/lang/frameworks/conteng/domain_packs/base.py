"""Base Domain Pack Interface

Defines the common interface for all domain packs in the Context Engineering system.
Domain packs provide domain-specific knowledge, templates, and configurations.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..templates import ContextTemplate


class BaseDomainPack(ABC):
    """Base class for all domain packs

    A domain pack provides:
    - Context templates for different agent methods
    - Domain-specific knowledge assets
    - Workflow patterns and templates
    - Tool selection guides
    - Conditional logic templates
    - Safety and compliance constraints
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.workflow_templates: dict[str, Any] = {}
        self.knowledge_assets: dict[str, Any] = {}
        self.conditional_templates: dict[str, Any] = {}
        self.tool_guides: dict[str, Any] = {}

    @abstractmethod
    def get_context_template(self, method: str, config: Any | None = None) -> ContextTemplate:
        """Get context template for a specific agent method

        Args:
            method: Agent method name (plan, solve, chat, use, remember)
            config: Domain-specific configuration object

        Returns:
            Context template configured for the method and domain
        """
        pass

    @abstractmethod
    def validate_configuration(self, config: Any) -> bool:
        """Validate domain-specific configuration

        Args:
            config: Domain-specific configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    def get_available_workflows(self) -> list[str]:
        """Get list of available workflow templates"""
        return list(self.workflow_templates.keys())

    def get_available_knowledge_assets(self) -> list[str]:
        """Get list of available knowledge assets"""
        return list(self.knowledge_assets.keys())

    def get_available_conditional_templates(self) -> list[str]:
        """Get list of available conditional templates"""
        return list(self.conditional_templates.keys())

    def get_supported_methods(self) -> list[str]:
        """Get list of supported agent methods"""
        return ["plan", "solve", "chat", "use", "remember", "recall"]

    def get_domain_info(self) -> dict[str, Any]:
        """Get information about this domain pack"""
        return {
            "domain": self.domain,
            "workflows": self.get_available_workflows(),
            "knowledge_assets": self.get_available_knowledge_assets(),
            "conditional_templates": self.get_available_conditional_templates(),
            "supported_methods": self.get_supported_methods(),
        }
