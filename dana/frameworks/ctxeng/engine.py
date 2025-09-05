"""
Context Engine - Main orchestrator for context engineering operations.
"""

import logging
from typing import Any

from .template_manager import TemplateManager

logger = logging.getLogger(__name__)


class ContextEngine:
    """Main orchestrator for context engineering operations."""

    def __init__(self, format_type: str = "xml", max_tokens: int = 1500, relevance_threshold: float = 0.7):
        """
        Initialize the context engine.

        Args:
            format_type: Output format ("xml" or "text")
            max_tokens: Maximum tokens for context assembly
            relevance_threshold: Minimum relevance score for context pieces
        """
        self.format_type = format_type
        self.max_tokens = max_tokens
        self.relevance_threshold = relevance_threshold

        # Initialize components
        self._resources: dict[str, Any] = {}
        self._workflows: dict[str, Any] = {}
        self._template_manager = TemplateManager()
        self._setup_assembler()

    def _setup_assembler(self):
        """Set up the appropriate context assembler."""
        # Note: We don't need to instantiate base classes here
        # The actual assembly is handled by the template manager
        pass

    def add_resource(self, name: str, resource: Any) -> None:
        """Add a resource that can provide context."""
        self._resources[name] = resource
        logger.debug(f"Added resource: {name}")

    def add_workflow(self, name: str, workflow: Any) -> None:
        """Add a workflow that can provide context."""
        self._workflows[name] = workflow
        logger.debug(f"Added workflow: {name}")

    def discover_resources(self, obj: Any) -> None:
        """Automatically discover and register resources from an object."""
        # Use AgentState integration
        if hasattr(obj, "state") and obj.state:
            agent_state = obj.state
            if hasattr(agent_state, "discover_resources_for_ctxeng"):
                resources = agent_state.discover_resources_for_ctxeng()
                for name, resource in resources.items():
                    self.add_resource(name, resource)
                logger.info(f"Discovered {len(resources)} resources from AgentState")
                return

        logger.warning("Object does not have AgentState - no resources discovered")

    @classmethod
    def from_agent_state(cls, agent_state: Any) -> "ContextEngine":
        """Create ContextEngine from centralized AgentState.

        Args:
            agent_state: The centralized agent state

        Returns:
            Configured ContextEngine instance
        """
        engine = cls()

        # Discover all resources from AgentState
        if hasattr(agent_state, "discover_resources_for_ctxeng"):
            resources = agent_state.discover_resources_for_ctxeng()
            for name, resource in resources.items():
                engine.add_resource(name, resource)

        return engine

    def assemble_from_state(self, agent_state: Any, template: str | None = None, **options) -> str:
        """Assemble context directly from AgentState.

        Args:
            agent_state: The centralized agent state
            template: Template name (auto-detected if None)
            **options: Additional assembly options

        Returns:
            Optimized prompt string
        """
        # Get unified context from AgentState
        if hasattr(agent_state, "get_llm_context"):
            context = agent_state.get_llm_context(depth=options.get("depth", "standard"))
        else:
            context = {}

        # Extract query from context
        query = context.get("query", "")

        # Use AgentMind priorities if available
        if hasattr(agent_state, "mind") and agent_state.mind:
            try:
                priorities = agent_state.mind.assess_context_needs(getattr(agent_state, "problem_context", None), template or "general")
                context["context_priorities"] = priorities
            except Exception as e:
                logger.debug(f"Could not assess context needs: {e}")

        # Assemble with template
        return self.assemble(query, context, template=template, **options)

    def assemble(self, query: str, context: dict[str, Any] | None = None, template: str | None = None, **options) -> str:
        """
        Assemble optimized context for the query.

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

        # Collect context from resources
        resource_context = self._collect_resource_context(query, template, options)

        # Merge with provided context
        all_context = {**resource_context, **context}

        # Get template and assemble
        template_obj = self._template_manager.get_template(template, self.format_type)
        return template_obj.assemble(query, all_context, options)

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

    def _collect_resource_context(self, query: str, template: str, options: dict[str, Any]) -> dict[str, Any]:
        """Collect context from registered resources."""
        context = {}

        # Collect from resources
        for name, resource in self._resources.items():
            try:
                if hasattr(resource, "get_context_for"):
                    resource_context = resource.get_context_for(query, **options)
                    context.update(resource_context)
                elif hasattr(resource, "get_context"):
                    resource_context = resource.get_context(query, template, **options)
                    context.update(resource_context)
            except Exception as e:
                logger.warning(f"Resource {name} failed to provide context: {e}")

        # Collect from workflows
        for name, workflow in self._workflows.items():
            try:
                if hasattr(workflow, "get_execution_context"):
                    workflow_context = workflow.get_execution_context()
                    context[f"workflow_{name}"] = workflow_context
                if hasattr(workflow, "get_pattern_info"):
                    pattern_info = workflow.get_pattern_info()
                    context[f"pattern_{name}"] = pattern_info
            except Exception as e:
                logger.warning(f"Workflow {name} failed to provide context: {e}")

        return context

    @classmethod
    def from_agent(cls, agent: Any, **config) -> "ContextEngine":
        """Create a context engine configured for an agent."""
        ctx = cls(**config)
        ctx.discover_resources(agent)
        return ctx

    @classmethod
    def from_workflow(cls, workflow: Any, **config) -> "ContextEngine":
        """Create a context engine configured for a workflow."""
        ctx = cls(**config)
        ctx.discover_resources(workflow)
        return ctx

    @classmethod
    def from_sandbox(cls, sandbox: Any, **config) -> "ContextEngine":
        """Create a context engine configured for a sandbox."""
        ctx = cls(**config)
        ctx.discover_resources(sandbox)
        return ctx
