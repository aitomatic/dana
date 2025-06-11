"""
POET Objective Registry

Central registry for managing objective functions across domains and providing
runtime objective configuration and lookup services.
"""

from typing import Dict, List, Any, Optional, Set
from .base import ObjectiveFunction, MultiObjective
from .domain_objectives import get_domain_objectives
from opendxa.common.utils.logging import DXA_LOGGER


class POETObjectiveRegistry:
    """
    Central registry for POET objective functions.

    Manages domain-specific objectives, custom user objectives, and provides
    runtime configuration and lookup services for the POET learning system.
    """

    def __init__(self):
        self._domain_objectives: Dict[str, MultiObjective] = {}
        self._custom_objectives: Dict[str, ObjectiveFunction] = {}
        self._objective_cache: Dict[str, MultiObjective] = {}
        self._initialized_domains: Set[str] = set()

        # Load default domain objectives
        self._load_default_domains()

    def _load_default_domains(self):
        """Load default objectives for known domains."""
        default_domains = ["building_management", "llm_optimization", "financial_services"]

        for domain in default_domains:
            try:
                multi_obj = get_domain_objectives(domain)
                self._domain_objectives[domain] = multi_obj
                self._initialized_domains.add(domain)
                DXA_LOGGER.debug(f"Loaded default objectives for domain: {domain}")
            except Exception as e:
                DXA_LOGGER.warning(f"Failed to load default objectives for {domain}: {e}")

    def register_domain_objectives(self, domain: str, multi_objective: MultiObjective) -> None:
        """
        Register multi-objective configuration for a domain.

        Args:
            domain: Domain name (e.g., "building_management")
            multi_objective: Configured multi-objective for the domain
        """
        if domain in self._domain_objectives:
            DXA_LOGGER.warning(f"Overriding existing objectives for domain: {domain}")

        self._domain_objectives[domain] = multi_objective
        self._initialized_domains.add(domain)

        # Clear cache for this domain
        cache_keys_to_remove = [k for k in self._objective_cache.keys() if k.startswith(f"{domain}:")]
        for key in cache_keys_to_remove:
            del self._objective_cache[key]

        DXA_LOGGER.info(f"Registered objectives for domain: {domain}")

    def register_custom_objective(self, name: str, objective: ObjectiveFunction) -> None:
        """
        Register a custom objective function.

        Args:
            name: Unique name for the objective
            objective: Custom objective function
        """
        if name in self._custom_objectives:
            DXA_LOGGER.warning(f"Overriding existing custom objective: {name}")

        self._custom_objectives[name] = objective
        DXA_LOGGER.info(f"Registered custom objective: {name}")

    def get_domain_objectives(self, domain: str, **config_kwargs) -> MultiObjective:
        """
        Get multi-objective configuration for a domain.

        Args:
            domain: Domain name
            **config_kwargs: Domain-specific configuration parameters

        Returns:
            MultiObjective: Configured objectives for the domain

        Raises:
            ValueError: If domain is not registered and cannot be auto-loaded
        """
        # Create cache key including configuration
        config_key = ":".join(f"{k}={v}" for k, v in sorted(config_kwargs.items()))
        cache_key = f"{domain}:{config_key}"

        # Check cache first
        if cache_key in self._objective_cache:
            return self._objective_cache[cache_key]

        # Try to get from registered domains
        if domain in self._domain_objectives:
            base_multi_obj = self._domain_objectives[domain]

            # If no custom config, return base configuration
            if not config_kwargs:
                self._objective_cache[cache_key] = base_multi_obj
                return base_multi_obj

            # Create customized version
            customized = self._customize_objectives(base_multi_obj, config_kwargs)
            self._objective_cache[cache_key] = customized
            return customized

        # Try to auto-load domain
        try:
            multi_obj = get_domain_objectives(domain, **config_kwargs)
            self._objective_cache[cache_key] = multi_obj
            DXA_LOGGER.info(f"Auto-loaded objectives for domain: {domain}")
            return multi_obj
        except Exception as e:
            raise ValueError(f"Unknown domain '{domain}' and failed to auto-load: {e}")

    def _customize_objectives(self, base_multi_obj: MultiObjective, config_kwargs: Dict[str, Any]) -> MultiObjective:
        """
        Create customized version of multi-objective based on configuration.

        Args:
            base_multi_obj: Base multi-objective configuration
            config_kwargs: Customization parameters

        Returns:
            MultiObjective: Customized multi-objective
        """
        # For now, create new instance with same objectives but potentially different method
        method = config_kwargs.get("optimization_method", base_multi_obj.method)

        # Could add more sophisticated customization here:
        # - Weight adjustments
        # - Constraint modifications
        # - Objective additions/removals

        customized = MultiObjective(name=f"{base_multi_obj.name}_custom", objectives=base_multi_obj.objectives.copy(), method=method)

        return customized

    def get_custom_objective(self, name: str) -> Optional[ObjectiveFunction]:
        """
        Get a custom objective by name.

        Args:
            name: Name of the custom objective

        Returns:
            ObjectiveFunction: The custom objective, or None if not found
        """
        return self._custom_objectives.get(name)

    def list_domains(self) -> List[str]:
        """List all registered domains."""
        return list(self._initialized_domains)

    def list_custom_objectives(self) -> List[str]:
        """List all registered custom objectives."""
        return list(self._custom_objectives.keys())

    def get_domain_summary(self, domain: str) -> Dict[str, Any]:
        """
        Get summary information for a domain's objectives.

        Args:
            domain: Domain name

        Returns:
            Dict: Summary information including objectives, constraints, etc.
        """
        try:
            multi_obj = self.get_domain_objectives(domain)
            return multi_obj.get_objective_summary()
        except ValueError:
            return {"error": f"Domain '{domain}' not found"}

    def validate_metrics_for_domain(self, domain: str, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate that provided metrics are sufficient for domain objectives.

        Args:
            domain: Domain name
            metrics: Available metrics

        Returns:
            Dict: Validation result with missing metrics and warnings
        """
        try:
            multi_obj = self.get_domain_objectives(domain)

            required_metrics = set()
            for obj in multi_obj.objectives:
                required_metrics.add(obj.metric_name)

            available_metrics = set(metrics.keys())
            missing_metrics = required_metrics - available_metrics
            extra_metrics = available_metrics - required_metrics

            return {
                "valid": len(missing_metrics) == 0,
                "missing_metrics": list(missing_metrics),
                "extra_metrics": list(extra_metrics),
                "required_metrics": list(required_metrics),
                "coverage": len(available_metrics & required_metrics) / len(required_metrics) if required_metrics else 1.0,
            }

        except ValueError as e:
            return {"valid": False, "error": str(e), "missing_metrics": [], "extra_metrics": [], "required_metrics": [], "coverage": 0.0}

    def create_custom_multi_objective(
        self, name: str, objective_names: List[str], method: str = "constraint_satisfaction"
    ) -> MultiObjective:
        """
        Create custom multi-objective from registered objectives.

        Args:
            name: Name for the custom multi-objective
            objective_names: List of objective names to include
            method: Optimization method to use

        Returns:
            MultiObjective: Custom multi-objective configuration

        Raises:
            ValueError: If any objective names are not found
        """
        objectives = []

        for obj_name in objective_names:
            # Look in custom objectives first
            if obj_name in self._custom_objectives:
                objectives.append(self._custom_objectives[obj_name])
                continue

            # Look in domain objectives
            found = False
            for domain_multi_obj in self._domain_objectives.values():
                for obj in domain_multi_obj.objectives:
                    if obj.name == obj_name:
                        objectives.append(obj)
                        found = True
                        break
                if found:
                    break

            if not found:
                raise ValueError(f"Objective '{obj_name}' not found in registry")

        return MultiObjective(name=name, objectives=objectives, method=method)

    def clear_cache(self):
        """Clear the objective cache."""
        self._objective_cache.clear()
        DXA_LOGGER.debug("Cleared objective cache")

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the registry."""
        total_objectives = sum(len(multi_obj.objectives) for multi_obj in self._domain_objectives.values())
        total_objectives += len(self._custom_objectives)

        domain_stats = {}
        for domain, multi_obj in self._domain_objectives.items():
            objectives_by_type = {}
            for obj in multi_obj.objectives:
                obj_type = obj.type.value
                objectives_by_type[obj_type] = objectives_by_type.get(obj_type, 0) + 1

            domain_stats[domain] = {
                "total_objectives": len(multi_obj.objectives),
                "objectives_by_type": objectives_by_type,
                "optimization_method": multi_obj.method,
            }

        return {
            "total_domains": len(self._initialized_domains),
            "total_custom_objectives": len(self._custom_objectives),
            "total_objectives": total_objectives,
            "cache_size": len(self._objective_cache),
            "domain_stats": domain_stats,
        }


# Global registry instance
_global_registry = None


def get_global_registry() -> POETObjectiveRegistry:
    """Get the global objective registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = POETObjectiveRegistry()
    return _global_registry


def reset_global_registry():
    """Reset the global registry (mainly for testing)."""
    global _global_registry
    _global_registry = None
