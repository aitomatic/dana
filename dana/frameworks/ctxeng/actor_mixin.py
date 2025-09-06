"""ContextEngineerMixin mixin for Dana agents to utilize CTXENG context engineering capabilities."""

from abc import ABC
from typing import Any, Union

from dana.core.agent import ProblemContext

from .engine import ContextEngine
from .template_manager import TemplateManager


class ContextEngineerMixin(ABC):
    """Mixin that adds CTXENG context engineering capabilities to Dana agents.

    This mixin can be applied to AgentInstance to add comprehensive
    context engineering capabilities while maintaining compatibility
    with existing agent functionality.
    """

    def __init__(self, *args, **kwargs):
        # Extract CTXENG config before calling super()
        self._ctxeng_config = kwargs.pop("ctxeng_config", {})
        super().__init__(*args, **kwargs)
        self._initialize_ctxeng_engine()

    def _initialize_ctxeng_engine(self) -> None:
        """Initialize CTXENG context engineering engine."""
        self._context_engine = ContextEngine(
            format_type=self._ctxeng_config.get("format_type", "xml"),
            max_tokens=self._ctxeng_config.get("max_tokens", 1500),
            relevance_threshold=self._ctxeng_config.get("relevance_threshold", 0.7),
        )
        self._template_manager = TemplateManager()

    # ===================== Context Engineering Operations =====================

    def assemble_context(self, query: str, context: dict[str, Any] | None = None, template: str | None = None, **options) -> str:
        """Assemble optimized context for LLM interactions.

        Args:
            query: The user's query or problem statement
            context: Optional additional context data
            template: Template name (auto-detected if None)
            **options: Additional assembly options

        Returns:
            Optimized prompt string (XML or text format)
        """
        return self._context_engine.assemble(query=query, context=context, template=template, **options)

    def assemble_from_agent_state(self, agent_state: Any, template: str | None = None, **options) -> str:
        """Assemble context directly from AgentState.

        Args:
            agent_state: The centralized agent state
            template: Template name (auto-detected if None)
            **options: Additional assembly options

        Returns:
            Optimized prompt string
        """
        return self._context_engine.assemble_from_state(agent_state=agent_state, template=template, **options)

    def discover_and_register_resources(self, obj: Any) -> None:
        """Automatically discover and register context resources from an object.

        Args:
            obj: Object to discover resources from (agent, workflow, etc.)
        """
        self._context_engine.discover_resources(obj)

    def add_context_resource(self, name: str, resource: Any) -> None:
        """Add a resource that can provide context.

        Args:
            name: Name identifier for the resource
            resource: Resource object implementing context interface
        """
        self._context_engine.add_resource(name, resource)

    def add_context_workflow(self, name: str, workflow: Any) -> None:
        """Add a workflow that can provide context.

        Args:
            name: Name identifier for the workflow
            workflow: Workflow object implementing context interface
        """
        self._context_engine.add_workflow(name, workflow)

    def get_available_templates(self, format_type: str | None = None) -> list[str]:
        """Get list of available context templates.

        Args:
            format_type: Optional format type to filter by ("xml" or "text")

        Returns:
            List of available template names
        """
        return self._template_manager.list_templates(format_type)

    def get_template_info(self, template_name: str, format_type: str = "xml") -> dict[str, Any]:
        """Get information about a specific template.

        Args:
            template_name: Name of the template
            format_type: Format type ("xml" or "text")

        Returns:
            Dictionary with template information
        """
        template = self._template_manager.get_template(template_name, format_type)
        return {
            "name": template_name,
            "format": format_type,
            "required_context": template.get_required_context(),
            "optional_context": template.get_optional_context(),
        }

    def detect_optimal_template(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Auto-detect the optimal template for a query.

        Args:
            query: The user's query
            context: Optional context data

        Returns:
            Recommended template name
        """
        return self._context_engine._detect_template(query, context or {}, {})

    def assemble_for_problem_solving(
        self, problem: Union[str, ProblemContext], available_resources: list[Any] | None = None, **options
    ) -> str:
        """Assemble context specifically for problem-solving scenarios.

        Args:
            problem: Problem statement or ProblemContext
            available_resources: List of available resources
            **options: Additional assembly options

        Returns:
            Optimized problem-solving prompt
        """
        problem_str = problem if isinstance(problem, str) else problem.problem_statement
        context = {"problem_context": problem_str}

        if available_resources:
            context["available_resources"] = [str(r) for r in available_resources]

        return self.assemble_context(query=problem_str, context=context, template="problem_solving", **options)

    def assemble_for_conversation(self, user_message: str, conversation_history: list[str] | None = None, **options) -> str:
        """Assemble context for conversational interactions.

        Args:
            user_message: Current user message
            conversation_history: Previous conversation turns
            **options: Additional assembly options

        Returns:
            Optimized conversation prompt
        """
        context = {}
        if conversation_history:
            context["conversation_history"] = "\n".join(conversation_history)

        return self.assemble_context(query=user_message, context=context, template="conversation", **options)

    def assemble_for_analysis(self, analysis_query: str, data_context: dict[str, Any] | None = None, **options) -> str:
        """Assemble context for data analysis scenarios.

        Args:
            analysis_query: Analysis question or task
            data_context: Context about available data
            **options: Additional assembly options

        Returns:
            Optimized analysis prompt
        """
        context = data_context or {}
        return self.assemble_context(query=analysis_query, context=context, template="analysis", **options)

    def optimize_context_for_tokens(self, query: str, context: dict[str, Any], max_tokens: int | None = None, **options) -> str:
        """Assemble context with token optimization.

        Args:
            query: The user's query
            context: Context data to optimize
            max_tokens: Maximum token limit (uses config default if None)
            **options: Additional optimization options

        Returns:
            Token-optimized prompt string
        """
        if max_tokens:
            # Temporarily update max_tokens for this operation
            original_max_tokens = self._context_engine.max_tokens
            self._context_engine.max_tokens = max_tokens
            try:
                return self.assemble_context(query, context, **options)
            finally:
                self._context_engine.max_tokens = original_max_tokens
        else:
            return self.assemble_context(query, context, **options)

    # ===================== Integration with Dana Architecture =====================

    def get_context_engine_state(self) -> dict[str, Any]:
        """Get current context engine state for integration with AgentState."""
        return {
            "format_type": self._context_engine.format_type,
            "max_tokens": self._context_engine.max_tokens,
            "relevance_threshold": self._context_engine.relevance_threshold,
            "registered_resources": list(self._context_engine._resources.keys()),
            "registered_workflows": list(self._context_engine._workflows.keys()),
            "available_templates": self.get_available_templates(),
            "config": self._ctxeng_config,
        }

    def set_context_engine_state(self, engine_state: dict[str, Any]) -> None:
        """Set context engine state from AgentState."""
        if "config" in engine_state:
            self._ctxeng_config = engine_state["config"]
            self._initialize_ctxeng_engine()

    def sync_with_agent_mind(self) -> None:
        """Synchronize CTXENG context with AgentMind memory systems."""
        if hasattr(self, "state") and hasattr(self.state, "mind"):
            # Store context engine summary in agent memory
            context_summary = self.get_context_engine_state()
            self.state.mind.form_memory({"type": "semantic", "key": "ctxeng_engine_state", "value": context_summary, "importance": 0.8})

    def contribute_to_context(self, problem_context: ProblemContext, context_depth: str = "standard") -> dict[str, Any]:
        """Contribute context engineering capabilities to ContextEngine."""
        context_contribution = {
            "context_engine_available": True,
            "format_type": self._context_engine.format_type,
            "max_tokens": self._context_engine.max_tokens,
            "registered_resources_count": len(self._context_engine._resources),
        }

        if context_depth in ["standard", "comprehensive"]:
            # Add template information
            available_templates = self.get_available_templates()
            context_contribution["available_templates"] = available_templates

            # Add resource information
            if self._context_engine._resources:
                context_contribution["registered_resources"] = list(self._context_engine._resources.keys())

        return context_contribution

    def enhance_problem_context(self, problem_context: ProblemContext) -> ProblemContext:
        """Enhance a ProblemContext with context engineering capabilities.

        Args:
            problem_context: Original problem context

        Returns:
            Enhanced problem context with additional context data
        """
        # Assemble context for the problem
        enhanced_context = self.assemble_for_problem_solving(problem_context)

        # Add context engineering metadata to constraints
        problem_context.constraints.update(
            {
                "context_engine_enhanced": True,
                "context_template": "problem_solving",
                "context_length": len(enhanced_context),
            }
        )

        return problem_context

    def create_context_engine_from_agent(self, **config) -> ContextEngine:
        """Create a ContextEngine instance configured for this agent.

        Args:
            **config: Additional configuration options

        Returns:
            Configured ContextEngine instance
        """
        return ContextEngine.from_agent(self, **config)

    def create_context_engine_from_state(self, agent_state: Any, **config) -> ContextEngine:
        """Create a ContextEngine instance from AgentState.

        Args:
            agent_state: The centralized agent state
            **config: Additional configuration options

        Returns:
            Configured ContextEngine instance
        """
        return ContextEngine.from_agent_state(agent_state, **config)

    # ===================== Static Methods for Mixin Application =====================

    @classmethod
    def apply_to_instance(cls, agent_instance: Any, ctxeng_config: dict[str, Any] | None = None) -> None:
        """Apply ContextEngineerMixin mixin to existing agent instance."""
        # This is a simplified implementation - in practice would need more careful mixing
        instance_class = type(agent_instance)

        # Create new class that includes ContextEngineerMixin
        class CTXENGEnhanced(instance_class, ContextEngineerMixin):
            pass

        # Replace the instance's class
        agent_instance.__class__ = CTXENGEnhanced

        # Initialize CTXENG components
        agent_instance._ctxeng_config = ctxeng_config or {}
        agent_instance._initialize_ctxeng_engine()
