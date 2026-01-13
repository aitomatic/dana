"""
Context Engineering Integration with Dana

Provides integration points with Dana's agent system, reason() calls,
and POET framework for seamless context engineering adoption.
"""

from typing import Any
from dataclasses import dataclass
import logging
from datetime import datetime

from .templates import ContextInstance, ContextSpec
from .architect import ContextArchitect
from .registry import get_registry
from .optimization import RuntimeContextOptimizer, ContextPerformanceMetrics


logger = logging.getLogger(__name__)


@dataclass
class AgentContextConfig:
    """Configuration extracted from agent blueprint for context engineering"""

    # Core agent identity
    agent_type: str
    domain: str | None = None
    specialization: str | None = None
    experience_level: str | None = None
    compliance_focus: bool = False

    # Optional explicit context control
    context_template: str | None = None
    knowledge_domains: list[str] | None = None
    policies: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/caching"""
        return {
            "agent_type": self.agent_type,
            "domain": self.domain,
            "specialization": self.specialization,
            "experience_level": self.experience_level,
            "compliance_focus": self.compliance_focus,
            "context_template": self.context_template,
            "knowledge_domains": self.knowledge_domains,
            "policies": self.policies,
        }


class ConEngIntegration:
    """Main integration class for Dana context engineering"""

    def __init__(self):
        self.registry = get_registry()
        self.architect = ContextArchitect(self.registry)
        self.optimizer = RuntimeContextOptimizer()
        self._agent_contexts: dict[str, ContextInstance] = {}

        # Integration state
        self.enabled = True
        self.telemetry_enabled = True

    def enhance_agent_method(
        self, method_name: str, agent_config: AgentContextConfig, task_description: str, existing_context: Any | None = None
    ) -> ContextInstance | None:
        """Enhance agent method with context engineering

        Args:
            method_name: Agent method (plan, solve, chat, use, remember)
            agent_config: Agent blueprint configuration
            task_description: Description of the task
            existing_context: Any existing context to merge

        Returns:
            Enhanced context instance or None if CE disabled
        """

        if not self.enabled:
            return existing_context

        start_time = datetime.now()

        try:
            # Create context specification
            spec = self._create_context_spec(method_name, agent_config, task_description)

            # Check cache first
            cache_key = spec.resolve_key()
            cached_context = self.optimizer.get_cached_context(cache_key)
            if cached_context:
                # Record cache hit
                self._record_performance_metrics(
                    spec,
                    assembly_time_ms=0.1,  # Minimal time for cache hit
                    cache_hit=True,
                    success=True,
                )
                return cached_context

            # Build context using architect
            context = self.architect.build_context(spec)

            # Cache the result
            self.optimizer.cache_context(cache_key, context)

            # Record performance metrics
            assembly_time = (datetime.now() - start_time).total_seconds() * 1000
            self._record_performance_metrics(spec, assembly_time_ms=assembly_time, cache_hit=False, success=True, context=context)

            return context

        except Exception as e:
            logger.error(f"Context engineering failed for {method_name}: {e}")

            # Record failure metrics
            assembly_time = (datetime.now() - start_time).total_seconds() * 1000
            failure_spec = ContextSpec(
                template_name=f"{agent_config.domain or 'unknown'}_{method_name}",
                template_version="latest",
                overrides={
                    "domain": agent_config.domain or "unknown",
                    "task": task_description,
                    "agent_type": agent_config.agent_type,
                    "method": method_name,
                },
            )
            self._record_performance_metrics(failure_spec, assembly_time_ms=assembly_time, cache_hit=False, success=False)

            return existing_context

    def _create_context_spec(self, method_name: str, agent_config: AgentContextConfig, task_description: str) -> ContextSpec:
        """Create context specification from agent config"""

        # Determine template name based on domain and method
        template_name = agent_config.context_template or f"{agent_config.domain or 'general'}_{method_name}"

        # Create overrides from agent config
        overrides = {
            "domain": agent_config.domain or "general",
            "task": task_description,
            "agent_type": agent_config.agent_type,
            "method": method_name,
            "specialization": agent_config.specialization,
            "experience_level": agent_config.experience_level,
            "compliance_required": agent_config.compliance_focus,
            "knowledge_domains": agent_config.knowledge_domains,
            "policies": agent_config.policies or {},
        }

        return ContextSpec(
            template_name=template_name,
            template_version="latest",
            overrides=overrides,
            additional_context={"task_description": task_description},
        )

    def _record_performance_metrics(
        self, spec: ContextSpec, assembly_time_ms: float, cache_hit: bool, success: bool, context: ContextInstance | None = None
    ):
        """Record performance metrics for optimization"""

        if not self.telemetry_enabled:
            return

        metrics = ContextPerformanceMetrics(
            context_signature=spec.resolve_key(),
            task_type=spec.overrides.get("method", "unknown"),
            domain=spec.overrides.get("domain", "unknown"),
            assembly_time_ms=assembly_time_ms,
            token_count=context.total_tokens if context else 0,
            success=success,
            cache_hit=cache_hit,
            knowledge_assets_used=len(context.knowledge_chunks) if context else 0,
        )

        self.optimizer.record_performance(metrics)

    def extract_agent_config(self, agent_instance: Any) -> AgentContextConfig:
        """Extract context configuration from Dana agent instance

        This is a placeholder - real implementation would inspect
        the agent's blueprint fields and extract relevant configuration.
        """

        # Default config
        config = AgentContextConfig(agent_type=type(agent_instance).__name__)

        # Extract common blueprint fields if they exist
        if hasattr(agent_instance, "domain"):
            config.domain = agent_instance.domain

        if hasattr(agent_instance, "specialization"):
            config.specialization = agent_instance.specialization

        if hasattr(agent_instance, "experience_level"):
            config.experience_level = agent_instance.experience_level

        if hasattr(agent_instance, "compliance_focus"):
            config.compliance_focus = bool(agent_instance.compliance_focus)

        # Extract optional explicit context fields
        if hasattr(agent_instance, "context_template"):
            config.context_template = agent_instance.context_template

        if hasattr(agent_instance, "knowledge_domains"):
            config.knowledge_domains = agent_instance.knowledge_domains

        if hasattr(agent_instance, "policies"):
            config.policies = agent_instance.policies

        return config

    def enhance_reason_call(self, prompt: str, context: Any | None = None, domain: str | None = None, **kwargs) -> Any:
        """Enhance reason() call with context engineering

        This would be called by Dana's reason() implementation
        to optionally enhance contexts.
        """

        if not self.enabled or context is not None:
            # Don't override explicit context
            return context

        if domain:
            # Create minimal spec for non-agent reason() calls
            spec = ContextSpec(
                template_name=f"{domain}_reason",
                template_version="latest",
                overrides={
                    "domain": domain,
                    "task": prompt[:100],  # Truncate long prompts
                    "agent_type": "standalone_reason",
                    "method": "reason",
                },
            )

            try:
                enhanced_context = self.architect.build_context(spec)
                return enhanced_context
            except Exception as e:
                logger.warning(f"Failed to enhance reason() call: {e}")

        return context

    def get_performance_report(self, domain: str | None = None) -> dict[str, Any]:
        """Get performance report for monitoring"""

        base_stats = self.optimizer.get_stats()
        performance_analysis = self.optimizer.analyze_performance(domain)
        recommendations = self.optimizer.generate_recommendations(domain)

        return {
            "integration_status": {
                "enabled": self.enabled,
                "telemetry_enabled": self.telemetry_enabled,
                "domains_available": self.registry.list_domains(),
                "timestamp": datetime.now().isoformat(),
            },
            "performance": performance_analysis,
            "cache_performance": base_stats["cache_stats"],
            "recommendations": [
                {
                    "type": r.recommendation_type,
                    "description": r.description,
                    "impact_estimate": r.impact_estimate,
                    "confidence": r.confidence,
                }
                for r in recommendations
            ],
        }

    def enable(self):
        """Enable context engineering integration"""
        self.enabled = True
        logger.info("Context engineering integration enabled")

    def disable(self):
        """Disable context engineering integration"""
        self.enabled = False
        logger.info("Context engineering integration disabled")

    def clear_cache(self):
        """Clear all caches"""
        self.optimizer.cache.clear()
        self.registry.clear_cache()
        logger.info("Context engineering caches cleared")


# Global integration instance
_global_integration: ConEngIntegration | None = None


def get_integration() -> ConEngIntegration:
    """Get the global context engineering integration"""
    global _global_integration
    if _global_integration is None:
        _global_integration = ConEngIntegration()
    return _global_integration


# Integration helper functions for Dana runtime


def enhance_agent_method(method_name: str, agent_instance: Any, task: str, context: Any = None) -> Any:
    """Helper function for Dana agent method enhancement"""
    integration = get_integration()
    agent_config = integration.extract_agent_config(agent_instance)
    return integration.enhance_agent_method(method_name, agent_config, task, context)


def enhance_reason(prompt: str, context: Any = None, domain: str = None, **kwargs) -> Any:
    """Helper function for Dana reason() enhancement"""
    integration = get_integration()
    return integration.enhance_reason_call(prompt, context, domain, **kwargs)
